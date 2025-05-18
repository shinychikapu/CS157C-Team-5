import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './index.css'
import App from './App'
import Login from './Login';
import Register from './Register';

const token = localStorage.getItem('access_token');

createRoot(document.getElementById('root')).render(
  <StrictMode>
      <BrowserRouter>
      <Routes>
        <Route path="/" element={token ? <App /> : <Navigate to="/login" />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
