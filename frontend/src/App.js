import React, { useState, useEffect } from 'react';
import SqlGenerator from './components/SqlGenerator';
import AuthForm from './components/AuthForm';
import SqlController from './controllers/SqlController';
import './App.css';

function App() {
  const [token, setToken] = useState(null);
  const sqlController = SqlController();

  useEffect(() => {
    // Check if user is already logged in
    const savedToken = localStorage.getItem('token');
    if (savedToken) {
      setToken(savedToken);
    }
  }, []);

  const handleAuthSuccess = (newToken) => {
    setToken(newToken);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('email');
    setToken(null);
  };

  if (!token) {
    return <AuthForm onSuccess={handleAuthSuccess} />;
  }

  return (
    <div className="App">
      <div className="app-header">
        <h1>🚀 Arquitecto SQL</h1>
        <button className="logout-btn" onClick={handleLogout}>
          Cerrar Sesión
        </button>
      </div>
      <SqlGenerator controller={sqlController} token={token} />
    </div>
  );
}

export default App;
