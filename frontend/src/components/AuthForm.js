import React, { useState } from 'react';
import apiClient from '../utils/apiClient';
import './AuthForm.css';

function AuthForm({ onSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('file_user@example.com');
  const [password, setPassword] = useState('Passw0rd!');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const payload = isLogin 
        ? { email, password }
        : { email, password, full_name: fullName };

      const response = await apiClient.post(endpoint, payload);
      const data = response.data;

      // Save token and user info
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('email', data.email);
      
      // Notify parent component
      onSuccess(data.access_token);
    } catch (err) {
      const message = err?.response?.data?.detail || err.message || 'Authentication failed';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>🚀 Arquitecto SQL</h1>
        <p className="subtitle">Transforma lenguaje natural en SQL</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="tu@email.com"
              required
            />
          </div>

          {!isLogin && (
            <div className="form-group">
              <label>Nombre Completo</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="John Doe"
                required
              />
            </div>
          )}

          <div className="form-group">
            <label>Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" disabled={loading} className="submit-btn">
            {loading ? 'Procesando...' : (isLogin ? 'Iniciar Sesión' : 'Registrarse')}
          </button>
        </form>

        <div className="toggle-auth">
          <p>
            {isLogin ? '¿No tienes cuenta? ' : '¿Ya tienes cuenta? '}
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
              }}
              className="link-btn"
            >
              {isLogin ? 'Regístrate' : 'Inicia sesión'}
            </button>
          </p>
        </div>

        <div className="demo-hint">
          💡 Demo: file_user@example.com / Passw0rd!
        </div>
      </div>
    </div>
  );
}

export default AuthForm;
