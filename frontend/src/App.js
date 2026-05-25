import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import UserProvider from './contexts/UserContext';
import RequireAuth from './components/RequireAuth';
import SqlGenerator from './components/SqlGenerator';
import AuthForm from './components/AuthForm';
import SqlController from './controllers/SqlController';
import InventoryDashboard from './components/InventoryDashboard';
import './App.css';

function App() {
  const sqlController = SqlController();

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('email');
    // reload to reset context
    window.location.href = '/login';
  };

  return (
    <BrowserRouter>
      <UserProvider>
        <div className="App">
          <div className="app-header">
            <h1>🚀 Arquitecto SQL</h1>
            <div>
              <button className="tab-btn" onClick={() => (window.location.href = '/sql')}>SQL</button>
              <button className="tab-btn" onClick={() => (window.location.href = '/inventory')}>Inventory</button>
              <button className="logout-btn" onClick={handleLogout}>Cerrar Sesión</button>
            </div>
          </div>

          <Routes>
            <Route path="/login" element={<AuthForm onSuccess={() => window.location.href = '/sql'} />} />
            <Route path="/" element={<Navigate to="/sql" replace />} />
            <Route path="/sql" element={<RequireAuth><SqlGenerator controller={sqlController} /></RequireAuth>} />
            <Route path="/inventory" element={<RequireAuth><InventoryDashboard /></RequireAuth>} />
          </Routes>
        </div>
      </UserProvider>
    </BrowserRouter>
  );
}

export default App;
