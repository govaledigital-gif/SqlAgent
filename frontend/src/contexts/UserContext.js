import React, { createContext, useState, useEffect } from 'react';
import apiClient from '../utils/apiClient';

export const UserContext = createContext({ user: null, setUser: () => {} });

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [initializing, setInitializing] = useState(true);

  const fetchUser = async () => {
    setInitializing(true);
    let token = null;
    try {
      token = localStorage.getItem('access_token');
    } catch (e) {
      token = null;
    }
    if (!token) {
      setUser(null);
      setInitializing(false);
      return;
    }
    try {
      const resp = await apiClient.get('/auth/me');
      setUser(resp.data);
    } catch (err) {
      // token invalid or expired - clear
      try { localStorage.removeItem('access_token'); } catch(e){}
      try { localStorage.removeItem('email'); } catch(e){}
      setUser(null);
    } finally {
      setInitializing(false);
    }
  };

  useEffect(() => {
    fetchUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <UserContext.Provider value={{ user, setUser, initializing }}>
      {children}
    </UserContext.Provider>
  );
};

export default UserProvider;
