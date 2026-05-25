import React, { useState, useEffect } from 'react';
import SqlGenerator from './components/SqlGenerator';
import AuthForm from './components/AuthForm';
import SqlController from './controllers/SqlController';
import InventoryDashboard from './components/InventoryDashboard';
import './App.css';

function App() {
  const [token, setToken] = useState(null);
  const sqlController = SqlController();
  const [tab, setTab] = useState('sql');

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
        <div>
          <button className="tab-btn" onClick={() => setTab('sql')} aria-pressed={tab==='sql'}>SQL</button>
          <button className="tab-btn" onClick={() => setTab('inventory')} aria-pressed={tab==='inventory'}>Inventory</button>
          <button className="logout-btn" onClick={handleLogout}>
            Cerrar Sesión
          </button>
        </div>
      </div>
      {tab === 'sql' ? (
        <SqlGenerator controller={sqlController} token={token} />
      ) : (
        <InventoryDashboard />
      )}
    </div>
  );
}

export default App;
