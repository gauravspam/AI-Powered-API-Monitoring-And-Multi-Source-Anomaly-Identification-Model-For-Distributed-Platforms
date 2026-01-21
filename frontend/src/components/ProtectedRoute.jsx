import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import { useContext } from 'react';
import { AuthContext } from '@/contexts/AuthContext';

export const ProtectedRoute = ({ children }) => {
  const authContext = useContext(AuthContext);
  const location = useLocation();

  // Safety check - if AuthContext is not available, redirect to login
  if (!authContext) {
    console.error('AuthContext is not available. Make sure AuthProvider wraps your app.');
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  const { isAuthenticated, isLoading } = authContext;

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          backgroundColor: 'background.default',
        }}
      >
        <CircularProgress size={60} />
      </Box>
    );
  }

  // Redirect to login if not authenticated, preserving intended destination
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // User is authenticated, render protected content
  return children;
};
