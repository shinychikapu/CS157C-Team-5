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

  const sendMessage = async () => {
    if (!input) return;
    setMessages([...messages, { sender: 'You', text: input }]);
    setInput('');

    try {
      const response = await fetch('/api/recipe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input }),
      });

      const data = await response.json();
      console.log(data)

      const markdown = data.markdown || 'No response received.';
      setMessages(prev => [...prev, { sender: 'Bot', markdown }]);
      setRecipes(data.recipes || []);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { sender: 'Bot', text: 'Error reaching server' }]);
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleKeyDown = (e) => {
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
        <button className="toggle-button" onClick={() => setIsOpen(!isOpen)}>
          <AiOutlineBars />
        </button>
        <span className="tools-text">{isOpen ? "Close sidebar" : "Open sidebar"}</span>
      </div>
      <div className={`sidebar ${isOpen ? 'open' : ''}`}>
        <p>Recipe List:</p>
        <ul>
          {recipes.map((recipe, index) => (
            <li key={index}>{recipe.name}</li>
          ))}
        </ul>
      </div>    
      <img src="/recipe logo transparent.png" alt="Logo" className="logo" />
      <button className="logout-button" onClick={handleLogout}>
        Logout
      </button>
      <div className="chat-container">
        <h2 className="chat-header">Recipe Chatbot</h2>
        <div className="chat-box">
          {messages.map((msg, i) => (
          <div
            className={`chat-message ${msg.sender === 'You' ? 'user-message' : 'bot-message'}`}
            key={i}
          >
            <div className={msg.sender === 'You' ? 'message-bubble' : ''}>
              <strong>{msg.sender}:</strong><br />
              {msg.markdown ? (
                <ReactMarkdown>{msg.markdown}</ReactMarkdown>
              ) : (
                msg.text
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
          <button onClick={sendMessage} className="chat-button">
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
