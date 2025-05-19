// src/App.jsx
import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { AiOutlineBars } from "react-icons/ai";
import './App.css';

function App() {
  const [messages, setMessages]       = useState([]);
  const [input, setInput]             = useState('');
  const [isOpen, setIsOpen]           = useState(false);
  const [recipes, setRecipes]         = useState([]);
  const [sessionId, setSessionId]     = useState(null);
  const [total, setTotal]             = useState(0);
  const [index, setIndex]             = useState(0);
  const [markdown, setMarkdown]       = useState("");
  const textareaRef                   = useRef(null);
  const navigate                      = useNavigate();
  const [savedRecipes, setSavedRecipes] = useState([]);
  const [modalRecipe, setModalRecipe] = useState(null);
  const dialogRef = useRef(null)


  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
    const token = localStorage.getItem("access_token");
    if (!token) return;

    fetch("/api/user/saved-recipes", {
      headers: { 
        "Authorization": `Bearer ${token}` 
      }
    })
    .then(res => {
      if (!res.ok) throw new Error(`Status ${res.status}`);
      return res.json();
    })
    .then(data => {
      // assuming your endpoint returns { recipes: [ { id, name, ... }, … ] }
      setSavedRecipes(data.recipes);
    })
    .catch(err => {
      console.error("Could not load saved recipes:", err);
    });
  }, [isOpen]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    setMessages(prev => [...prev, { sender: 'You', text: input }]);
    setInput('');
    setIndex(0);

    try {
      const res = await fetch('/api/recipe', {   
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input }),
      });
      if (!res.ok) throw new Error(`Server error ${res.status}`);

      const data = await res.json();
      const md   = data.markdown ?? "Sorry, no recipe.";
      setSessionId(data.session_id);
      setTotal(data.total);
      setIndex(data.index);
      setMarkdown(md);
      setMessages(prev => [...prev, { sender: 'Bot', markdown: md }]);
      setRecipes(data.recipes ?? []);
    } catch (err) {
      console.error(err);
      setMessages(prev => [
        ...prev,
        { sender: 'Bot', text: '❌ Error reaching server' }
      ]);
    }
  };

  const nextRecipe = async () => {
    if (!sessionId) return alert("No session. Ask a question first.");
    setMessages(prev => [...prev, { sender: 'You', text: 'Next recipe' }]);

    try {
      const res = await fetch('/api/recipe/next', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Unknown error');
      }
      const data = await res.json();
      const md   = data.markdown ?? "Sorry, no recipe.";
      setIndex(data.index);
      setMarkdown(md);
      setRecipes(data.recipes);
      setMessages(prev => [...prev, { sender: 'Bot', markdown: md }]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [
        ...prev,
        { sender: 'Bot', text: `❌ ${err.message}` }
      ]);
    }
  };

  const saveRecipe = async () => {
    if (!recipes.length || index < 0 || index >= recipes.length) {
      return alert("No recipe to save");
    }
    const token = localStorage.getItem("access_token");
    console.log("→ sending token:", token);
    const recipeId = recipes[index].id;
    try {
      const res = await fetch('/api/user/save-recipe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ recipe_id: recipeId }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to save');
      alert(`Saved recipe ${data.recipe_saved}!`);
    } catch (err) {
      console.error('Save failed', err);
      alert('Error saving recipe: ' + err.message);
    }
  };

  const openRecipe = async (id) => {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`/api/user/saved-recipe/${id}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) return console.error("failed to load recipe", res.status);
    const { markdown, name } = await res.json();
    console.log(markdown);
    setModalRecipe({ id, name, markdown });
  };

  const closeModal = () => setModalRecipe(null);

  const handleKeyDown = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    navigate('/login');
  };

  return (
    <div className="wrapper">
      <div className="tools">
        <button className="toggle-button" onClick={() => setIsOpen(o=>!o)}>
          <AiOutlineBars />
        </button>
        <span className="tools-text">
          {isOpen ? "Close sidebar" : "Open sidebar"}
        </span>
      </div>

      <div className={`sidebar ${isOpen ? 'open' : ''}`}>
        <button onClick={()=>setIsOpen(false)}>×</button>
        <p>— Your Saved Recipes —</p>
        {savedRecipes.length === 0 ? (
        <p><em>No recipes saved yet.</em></p>
        ) : (
            <div className="saved-list">
              {savedRecipes.map(r => (
                <div key={r.id} className="saved-list-item">
                  <button
                    className="link-button"
                    onClick={() => openRecipe(r.id)}
                  >
                    {r.name.charAt(0).toUpperCase() + r.name.slice(1)}
                  </button>
                </div>
              ))}
            </div>
        )}
        </div>

          {/* only renders when modalRecipe is non-null */}
      {modalRecipe && (
        <div className="modal-backdrop" onClick={closeModal}>
          <div className="my-modal" onClick={e => e.stopPropagation()}>
            <header>
              <button padding = "16px 32px" onClick={closeModal}>×</button>
            </header>
            <div className="modal-content markdown-body">
              <ReactMarkdown>
                {modalRecipe.markdown}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      )}

      <button className="logout-button" onClick={handleLogout}>
        Logout
      </button>

      <img src="/recipe logo transparent.png" alt="Logo" className="logo" />
        
      <div className="chat-container">
        <h2 className="chat-header">Recipe Chatbot</h2>
        <div className="chat-box">
          {messages.map((msg,i)=>(
            <div key={i} className={`chat-message ${msg.sender==='You'?'user-message':'bot-message'}`}>
              <div className={msg.sender==='You'?'message-bubble':''}>
                <strong>{msg.sender}:</strong><br/>
                {msg.sender==='Bot' && msg.markdown ? (
                  <div className="markdown-body">
                    <ReactMarkdown>{msg.markdown}</ReactMarkdown>
                    <button onClick={saveRecipe}>Save</button>
                    <button onClick={nextRecipe} className="chat-button">Next</button>
                  </div>
                ) : (
                  <p>{msg.text}</p>
                )}
              </div>
            </div>
          ))}
        </div>
          
        <div className="chat-input-area">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={e=>setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask something..."
            className="chat-input"
          />
          <button onClick={sendMessage} className="chat-button">Send</button>
        </div>
      </div>
    </div>

    
  );
}

export default App;
