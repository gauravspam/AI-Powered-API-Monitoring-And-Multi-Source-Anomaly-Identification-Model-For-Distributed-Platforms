import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    withCredentials: true,
});

// Request interceptor to add CSRF token to requests
api.interceptors.request.use(
    (config) => {
        // Only add CSRF token for state-changing operations
        const method = config.method?.toUpperCase();
        if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
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

// Response interceptor to handle 401s (Session Expired)
api.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        if (error.response && error.response.status === 401) {
            // Prevent infinite reload loops if already on login page
            if (window.location.pathname !== '/login') {
                // Optional: Clear client-side storage if you use it for user details
                // localStorage.removeItem('user');

                // Force redirect to login page
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default api;











// import axios from 'axios';

// const api = axios.create({
//     baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
//     withCredentials: true,
// });

// // Request interceptor to add CSRF token to requests
// api.interceptors.request.use(
//     (config) => {
//         // Only add CSRF token for state-changing operations
//         const method = config.method?.toUpperCase();
//         if (method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH') {
//             // Get CSRF token from cookie if available
//             const cookies = document.cookie.split(';');
//             const csrfCookie = cookies.find(cookie => cookie.trim().startsWith('XSRF-TOKEN='));
//             if (csrfCookie) {
//                 const csrfToken = decodeURIComponent(csrfCookie.split('=')[1]);
//                 config.headers['X-XSRF-TOKEN'] = csrfToken;
//             }
//         }
//         return config;
//     },
//     (error) => {
//         return Promise.reject(error);
//     }
// );

// // Response interceptor to handle 401s (Session Expired)
// api.interceptors.response.use(
//     (response) => {
//         return response;
//     },
//     (error) => {
//         if (error.response && error.response.status === 401) {
//             // 1. Clear any local storage flags if you use them
//             // localStorage.removeItem('user');

//             // 2. Redirect to login page
//             // Since we are outside a React component, we use window.location
//             if (window.location.pathname !== '/login') {
//                 window.location.href = '/login';
//             }
//         }
//         return Promise.reject(error);
//     }
// );

// export default api;
