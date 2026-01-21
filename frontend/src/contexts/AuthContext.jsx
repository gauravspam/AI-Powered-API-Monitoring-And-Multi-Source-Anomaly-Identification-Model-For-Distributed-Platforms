import { createContext, useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '@/api/http';

// Auth Context
export const AuthContext = createContext({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => {},
  logout: async () => {},
  refreshUser: async () => {},
});

// Helper to get CSRF token from cookie
const getCsrfToken = () => {
  const cookies = document.cookie.split(';');
  const csrfCookie = cookies.find(cookie => cookie.trim().startsWith('XSRF-TOKEN='));
  return csrfCookie ? decodeURIComponent(csrfCookie.split('=')[1]) : null;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  // Check if user is authenticated on mount
  const checkAuth = useCallback(async () => {
    try {
      setIsLoading(true);
      
      // Check if httpOnly cookie exists by calling /auth/me
      const response = await api.get('/auth/me', {
        withCredentials: true, // Important: sends cookies
        timeout: 5000, // 5 second timeout
      });
      
      if (response.data && response.data.user) {
        setUser(response.data.user);
        setIsAuthenticated(true);
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (error) {
      // Not authenticated or token expired - this is expected for first-time visitors
      // Only log if it's not a 401 (which is expected)
      if (error.response?.status !== 401 && !error.code?.includes('ECONNABORTED')) {
        console.error('Auth check error:', error);
      }
      setUser(null);
      setIsAuthenticated(false);
      // Clear any stale state
      document.cookie = 'authToken=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Strict';
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Login function
  const login = useCallback(async (email, password) => {
    try {
      setIsLoading(true);
      
      // Get CSRF token first if needed
      await api.get('/auth/csrf', { withCredentials: true });
      
      const response = await api.post(
        '/auth/login',
        { email, password },
        {
          withCredentials: true, // Important: receives httpOnly cookies
          headers: {
            'X-XSRF-TOKEN': getCsrfToken() || '',
          },
        }
      );

      if (response.data && response.data.user) {
        setUser(response.data.user);
        setIsAuthenticated(true);
        return { success: true, user: response.data.user };
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      const errorMessage = error.response?.data?.message || 
                          error.response?.data?.error || 
                          error.message || 
                          'Login failed. Please check your credentials.';
      
      setUser(null);
      setIsAuthenticated(false);
      return { success: false, error: errorMessage };
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Logout function
  const logout = useCallback(async () => {
    try {
      setIsLoading(true);
      
      // Call logout endpoint to clear server-side session
      await api.post(
        '/auth/logout',
        {},
        {
          withCredentials: true,
          headers: {
            'X-XSRF-TOKEN': getCsrfToken() || '',
          },
        }
      ).catch(() => {
        // Ignore errors on logout - we'll clear client-side anyway
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear client-side state regardless of API call success
      setUser(null);
      setIsAuthenticated(false);
      setIsLoading(false);
      
      // Clear any client-side cookies (backup)
      document.cookie = 'authToken=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Strict';
      document.cookie = 'XSRF-TOKEN=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Strict';
      
      // Redirect to login
      navigate('/login', { replace: true });
    }
  }, [navigate]);

  // Refresh user data
  const refreshUser = useCallback(async () => {
    try {
      const response = await api.get('/auth/me', {
        withCredentials: true,
      });
      
      if (response.data && response.data.user) {
        setUser(response.data.user);
        setIsAuthenticated(true);
        return { success: true, user: response.data.user };
      }
    } catch (error) {
      // If refresh fails, user is not authenticated
      setUser(null);
      setIsAuthenticated(false);
      return { success: false };
    }
  }, []);

  // Check auth on mount
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Setup axios interceptor to handle 401 errors globally
  useEffect(() => {
    let isLoggingOut = false; // Prevent infinite loops
    
    const interceptor = api.interceptors.response.use(
      (response) => response,
      async (error) => {
        // Only handle 401 if we're authenticated and not already logging out
        if (error.response?.status === 401 && isAuthenticated && !isLoggingOut) {
          // Prevent multiple simultaneous logout calls
          isLoggingOut = true;
          
          // Clear state immediately to prevent further API calls
          setUser(null);
          setIsAuthenticated(false);
          
          // Call logout (but don't await to prevent blocking)
          logout().finally(() => {
            isLoggingOut = false;
          });
        }
        return Promise.reject(error);
      }
    );

    return () => {
      api.interceptors.response.eject(interceptor);
    };
  }, [isAuthenticated, logout]);

  // Memoize context value
  const value = useMemo(
    () => ({
      user,
      isAuthenticated,
      isLoading,
      login,
      logout,
      refreshUser,
    }),
    [user, isAuthenticated, isLoading, login, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
