import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import UserProvider from './contexts/UserContext';
import RequireAuth from './components/RequireAuth';
import AuthForm from './components/AuthForm';
import InventoryDashboard from './components/InventoryDashboard';
import './App.css';

function AppInner() {
  const navigate = useNavigate();
  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('email');
    // navigate to login and let UserProvider re-check
    navigate('/login');
  };

  return (
    <div className="App">
      <div className="app-header">
        <h1>🚀 Arquitecto SQL</h1>
        <div>
          <button className="tab-btn" onClick={() => navigate('/inventory')}>Inventory</button>
          <button className="logout-btn" onClick={handleLogout}>Cerrar Sesión</button>
        </div>
      </div>

      <Routes>
        <Route path="/login" element={<AuthForm onSuccess={() => navigate('/inventory')} />} />
        <Route path="/" element={<Navigate to="/inventory" replace />} />
        <Route path="/inventory" element={<RequireAuth><InventoryDashboard /></RequireAuth>} />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <UserProvider>
        <AppInner />
      </UserProvider>
    </BrowserRouter>
  );
}

export default App;
