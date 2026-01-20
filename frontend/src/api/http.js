import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8080/api",
  withCredentials: true, // Important: enables sending/receiving httpOnly cookies
});

// Request interceptor to add CSRF token to requests
api.interceptors.request.use(
  (config) => {
    // Only add CSRF token for state-changing operations
    const method = config.method?.toUpperCase();
    if (method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH') {
      // Get CSRF token from cookie if available
      const cookies = document.cookie.split(';');
      const csrfCookie = cookies.find(cookie => cookie.trim().startsWith('XSRF-TOKEN='));
      if (csrfCookie) {
        const csrfToken = decodeURIComponent(csrfCookie.split('=')[1]);
        config.headers['X-XSRF-TOKEN'] = csrfToken;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;