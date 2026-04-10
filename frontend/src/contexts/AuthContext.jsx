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

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  // Check if user is authenticated on mount
  const checkAuth = useCallback(async () => {
    try {
      setIsLoading(true);
      
      // Bypass auth check - assume authenticated for demo purposes
      // Backend has no auth, so we simulate a logged-in user
      setUser({ id: 1, email: 'admin@api.local', role: 'admin' });
      setIsAuthenticated(true);
    } catch (error) {
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Login function
  const login = useCallback(async (email, password) => {
    try {
      setIsLoading(true);
      
      // Bypass actual auth - accept any credentials for demo
      setUser({ id: 1, email: email || 'admin@api.local', role: 'admin' });
      setIsAuthenticated(true);
      return { success: true, user: { id: 1, email: email || 'admin@api.local', role: 'admin' } };
    } catch (error) {
      const errorMessage = error.message || 'Login failed.';
      setUser(null);
      setIsAuthenticated(false);
      return { success: false, error: errorMessage };
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Logout function
  const logout = useCallback(async () => {
    setUser(null);
    setIsAuthenticated(false);
    setIsLoading(false);
    navigate('/login', { replace: true });
  }, [navigate]);

  // Refresh user data
  const refreshUser = useCallback(async () => {
    // Simulate refresh - still authenticated for demo
    setUser({ id: 1, email: 'admin@api.local', role: 'admin' });
    setIsAuthenticated(true);
    return { success: true, user: { id: 1, email: 'admin@api.local', role: 'admin' } };
  }, []);

  // Check auth on mount
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Setup axios interceptor to handle 401 errors globally
  useEffect(() => {
    const interceptor = api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          setUser(null);
          setIsAuthenticated(false);
          navigate('/login', { replace: true });
        }
        return Promise.reject(error);
      }
    );

    return () => {
      api.interceptors.response.eject(interceptor);
    };
  }, [navigate]);

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
