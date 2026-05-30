import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // consider adding `withCredentials: true` if switching to cookie-based auth
});

// Add token to every request
apiClient.interceptors.request.use(
  (config) => {
    let token = null;
    try {
      token = localStorage.getItem('access_token');
    } catch (e) {
      // localStorage unavailable (privacy mode or blocked) — proceed without token
      token = null;
    }
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle 401 responses
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth data and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('email');
      // prefer client-side navigation to /login
      try { window.location.href = '/login'; } catch (e) { /* ignore */ }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
