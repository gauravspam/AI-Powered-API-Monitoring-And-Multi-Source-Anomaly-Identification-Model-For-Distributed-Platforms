import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

api.interceptors.request.use(
  (config) => {
    const method = config.method?.toUpperCase();
    if (method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH') {
      const cookies = document.cookie.split(';');
      const csrfCookie = cookies.find(cookie => cookie.trim().startsWith('XSRF-TOKEN='));
      if (csrfCookie) {
        const csrfToken = decodeURIComponent(csrfCookie.split('=')[1]);
        config.headers['X-XSRF-TOKEN'] = csrfToken;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export async function apiRequest(method, url, body) {
  const config = { method, url };
  if (body) {
    config.data = body;
  }
  return api(config);
}

export default api;

export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8080';
export const ML_SERVICE_URL = import.meta.env.VITE_ML_SERVICE_URL || 'http://localhost:9000';