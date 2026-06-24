import axios from 'axios';

// Use the current window's hostname to construct the API URL
// This allows the frontend to connect to the backend whether accessed via localhost or a local IP
const apiBaseUrl = window.location.hostname === 'localhost' 
  ? 'http://localhost:8000/api' 
  : `http://${window.location.hostname}:8000/api`;

const api = axios.create({
  baseURL: apiBaseUrl,
});

// Add a request interceptor to attach the JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add a response interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
