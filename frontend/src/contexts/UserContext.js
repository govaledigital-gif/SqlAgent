import React, { createContext, useState, useEffect } from 'react';
import apiClient from '../utils/apiClient';

export const UserContext = createContext({ user: null, setUser: () => {} });

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  const fetchUser = async () => {
    const token = localStorage.getItem('token');
    if (!token) return;
    try {
      const resp = await apiClient.get('/auth/me');
      setUser(resp.data);
    } catch (err) {
      // token invalid or expired - clear
      localStorage.removeItem('token');
      localStorage.removeItem('email');
      setUser(null);
    }
  };

  useEffect(() => {
    fetchUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <UserContext.Provider value={{ user, setUser }}>
      {children}
    </UserContext.Provider>
  );
};

export default UserProvider;
