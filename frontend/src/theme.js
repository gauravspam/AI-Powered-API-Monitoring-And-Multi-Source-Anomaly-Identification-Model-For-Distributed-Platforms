import { createTheme } from '@mui/material/styles';

// Professional monitoring dashboard theme inspired by Grafana/Prometheus
// Deep blue primary + amber/orange accents for alerts
export const getTheme = (mode) => createTheme({
  palette: {
    mode,
    ...(mode === 'light'
      ? {
          // Light mode
          primary: {
            main: '#0d47a1', // Deep blue
            light: '#5472d3',
            dark: '#002171',
            contrastText: '#ffffff',
          },
          secondary: {
            main: '#fb8c00', // Amber/Orange
            light: '#ffbd45',
            dark: '#c25e00',
            contrastText: '#000000',
          },
          background: {
            default: '#f5f7fa',
            paper: '#ffffff',
          },
          error: {
            main: '#d32f2f',
          },
          warning: {
            main: '#f57c00',
          },
          success: {
            main: '#388e3c',
          },
          info: {
            main: '#0288d1',
          },
        }
      : {
          // Dark mode - optimized for monitoring
          primary: {
            main: '#42a5f5', // Lighter blue for dark bg
            light: '#80d6ff',
            dark: '#0077c2',
            contrastText: '#000000',
          },
          secondary: {
            main: '#ffa726', // Amber
            light: '#ffd95b',
            dark: '#c77800',
            contrastText: '#000000',
          },
          background: {
            default: '#0a1929', // Dark navy
            paper: '#132f4c',
          },
          error: {
            main: '#ef5350',
          },
          warning: {
            main: '#ff9800',
          },
          success: {
            main: '#66bb6a',
          },
          info: {
            main: '#29b6f6',
          },
        }),
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
    subtitle1: {
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundImage: 'none',
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
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 500,
        },
      },
    },
  },
});
