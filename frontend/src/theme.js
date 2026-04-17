import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: 'hsl(188, 80%, 42%)',
      light: 'hsl(188, 80%, 52%)',
      dark: 'hsl(188, 80%, 32%)',
    },
    secondary: {
      main: '#a855f7',
    },
    error: {
      main: '#ef4444',
    },
    warning: {
      main: '#f97316',
    },
    success: {
      main: '#22c55e',
    },
    info: {
      main: '#3b82f6',
    },
    background: {
      default: 'hsl(222, 20%, 8%)',
      paper: 'hsl(222, 18%, 11%)',
    },
    text: {
      primary: 'hsl(210, 20%, 88%)',
      secondary: 'hsl(210, 10%, 50%)',
    },
    divider: 'hsl(222, 14%, 20%)',
  },
  typography: {
    fontFamily: "'Inter', 'DM Sans', system-ui, sans-serif",
    fontSize: 14,
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarWidth: 'thin',
          '&::-webkit-scrollbar': {
            width: '6px',
            height: '6px',
          },
          '&::-webkit-scrollbar-thumb': {
            background: 'hsl(222, 14%, 20%)',
            borderRadius: '3px',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          backgroundColor: 'hsl(222, 18%, 11%)',
          color: 'hsl(210, 10%, 50%)',
          fontWeight: 500,
          fontSize: '0.75rem',
        },
      },
    },
  },
});

// Severity → color map used across pages
export const SEVERITY_COLORS = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#22c55e',
  NORMAL: '#6b7280',
  ACTIVE: '#ef4444',
  ACKNOWLEDGED: '#eab308',
  RESOLVED: '#22c55e',
  ERROR: '#ef4444',
  WARN: '#f97316',
  WARNING: '#f97316',
  INFO: '#3b82f6',
  DEBUG: '#6b7280',
  FATAL: '#ef4444',
};

export default theme;
