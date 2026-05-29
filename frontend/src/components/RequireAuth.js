import React, { useContext } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { UserContext } from '../contexts/UserContext';

const RequireAuth = ({ children }) => {
  const { user, initializing } = useContext(UserContext);
  const location = useLocation();

  if (initializing) {
    // while we check the token, don't redirect — show nothing or a loader
    return <div style={{padding:20}}>Cargando sesión...</div>;
  }

  if (!user) {
    // redirect to login page
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

export default RequireAuth;
