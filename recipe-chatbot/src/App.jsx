// src/App.jsx
import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { AiOutlineBars } from "react-icons/ai";
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [recipes, setRecipes] = useState([]);
  const textareaRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    // Add user bubble
    setMessages(prev => [...prev, { sender: 'You', text: input }]);
    setInput('');

    try {
      const res = await fetch('/api/recipe', {    // <-- use proxy
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input }),
      });

      if (!res.ok) {
        throw new Error(`Server error ${res.status}`);
      }

      const data = await res.json();
      const md   = data.markdown ?? "Sorry, no recipe.";
      console.log(data)
      // Add bot bubble with markdown
      setMessages(prev => [...prev, { sender: 'Bot', markdown: md }]);
      setRecipes(data.recipes || []);
    } catch (err) {
      console.error(err);
      setMessages(prev => [
        ...prev,
        { sender: 'Bot', text: '❌ Error reaching server' }
      ]);
    }
  };

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
        <button className="toggle-button" onClick={() => setIsOpen(open => !open)}>
          <AiOutlineBars />
        </button>
        <span className="tools-text">
          {isOpen ? "Close sidebar" : "Open sidebar"}
        </span>
      </div>

      <div className={`sidebar ${isOpen ? 'open' : ''}`}>
        <p>— Sidebar —</p>
        <p>Recipe List:</p>
        <ul>
          {recipes.map((recipe, index) => (
            <li key={index}>{recipe.name}</li>
          ))}
        </ul>
      </div>    
      <button className="logout-button" onClick={handleLogout}>
        Logout
      </button>

      <img src="/recipe logo transparent.png" alt="Logo" className="logo" />

      <div className="chat-container">
        <h2 className="chat-header">Recipe Chatbot</h2>
        <div className="chat-box">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`chat-message ${msg.sender === 'You' ? 'user-message' : 'bot-message'}`}
            >
              <div className={msg.sender === 'You' ? 'message-bubble' : ''}>
                <strong>{msg.sender}:</strong><br/>
                {msg.sender === 'Bot' && msg.markdown ? (
                  <ReactMarkdown>{msg.markdown}</ReactMarkdown>
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
            onChange={e => setInput(e.target.value)}
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
