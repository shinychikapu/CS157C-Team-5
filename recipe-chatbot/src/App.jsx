import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  const sendMessage = async () => {
    if (!input) return;
    setMessages([...messages, { sender: 'You', text: input }]);
    setInput('');

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input }),
      });

      const data = await response.json();
      const recipeList = data.recipes?.map((recipe, idx) => {
        return `• ${recipe.name}\n  - Description: ${recipe.description || 'N/A'}\n  - Instructions: ${recipe.steps || 'N/A'}\n`;
      }).join('\n') || 'No recipes found.';
      const tags = data.tags?.join(', ') || 'None';
      const ingredients = data.ingredients?.join(', ') || 'None';
      setMessages(prev => [...prev, 
        { sender: 'Bot', text: `${data.answer || 'No answer'}\n` +
          `Recipes:\n${recipeList}\n`}
      ]);
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

  return (
    <div className="wrapper">
      <img src="/recipe logo transparent.png" alt="Logo" className="logo" />
      <div className="chat-container">
        <h2 className="chat-header">Recipe Chatbot</h2>
        <div className="chat-box">
          {messages.map((msg, i) => (
            <div className="chat-message" key={i}>
              <strong>{msg.sender}:</strong> {msg.text}
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
