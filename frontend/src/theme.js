import { createTheme } from '@mui/material/styles';

// ─────────────────────────────────────────────────────────────────────────────
// Design tokens — immutable across both modes
// ─────────────────────────────────────────────────────────────────────────────
export const SEVERITY_COLORS = {
  CRITICAL: '#ef4444',
  HIGH:     '#f97316',
  MEDIUM:   '#eab308',
  LOW:      '#22c55e',
  NORMAL:   '#6b7280',
  // Status aliases
  ACTIVE:       '#ef4444',
  ACKNOWLEDGED: '#eab308',
  RESOLVED:     '#22c55e',
  // Log levels
  ERROR:   '#ef4444',
  WARN:    '#f97316',
  WARNING: '#f97316',
  INFO:    '#3b82f6',
  DEBUG:   '#6b7280',
  FATAL:   '#ef4444',
};

export const MODEL_COLORS = {
  'MSIF-LSTM':       'hsl(188, 80%, 42%)',
  'PLE-GRU':         '#f97316',
  'Hybrid Ensemble': '#a855f7',
};

// Shared typography + component overrides (mode-agnostic)
const sharedTypography = {
  fontFamily: "'Inter', 'DM Sans', system-ui, sans-serif",
  fontSize: 13,
  h4: { fontWeight: 700, fontSize: '1.5rem',  lineHeight: 1.2, fontVariantNumeric: 'tabular-nums lining-nums' },
  h5: { fontWeight: 700, fontSize: '1.25rem', lineHeight: 1.2, fontVariantNumeric: 'tabular-nums lining-nums' },
  h6: { fontWeight: 600, fontSize: '1rem',    lineHeight: 1.3 },
  body1: { fontSize: '0.875rem', lineHeight: 1.5 },
  body2: { fontSize: '0.8rem',   lineHeight: 1.5 },
  caption: { fontSize: '0.75rem', lineHeight: 1.4 },
};

const sharedShape = { borderRadius: 8 };

const sharedComponents = (mode) => ({
  MuiCssBaseline: {
    styleOverrides: {
      '*, *::before, *::after': { boxSizing: 'border-box' },
      html: { height: '100%' },
      body: {
        height: '100%',
        scrollbarWidth: 'thin',
        scrollbarColor: mode === 'dark'
          ? 'hsl(222, 14%, 22%) transparent'
          : 'hsl(222, 14%, 75%) transparent',
        '&::-webkit-scrollbar': { width: '5px', height: '5px' },
        '&::-webkit-scrollbar-track': { background: 'transparent' },
        '&::-webkit-scrollbar-thumb': {
          background: mode === 'dark' ? 'hsl(222, 14%, 22%)' : 'hsl(222, 14%, 75%)',
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
        fontSize: '0.8125rem',
      },
    },
  },
  MuiPaper: {
    styleOverrides: {
      root: { backgroundImage: 'none' },
    },
  },
  MuiTableCell: {
    styleOverrides: {
      head: {
        fontWeight: 600,
        fontSize: '0.6875rem',
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
        backgroundColor: mode === 'dark' ? 'hsl(222, 18%, 10%)' : '#f0f2f5',
        color: mode === 'dark' ? 'hsl(210, 10%, 50%)' : 'hsl(222, 20%, 42%)',
      },
    },
  },
  MuiToggleButton: {
    styleOverrides: {
      root: {
        textTransform: 'none',
        fontSize: '0.75rem',
        fontWeight: 500,
        padding: '3px 10px',
      },
    },
  },
  MuiChip: {
    styleOverrides: {
      root: { fontWeight: 500 },
    },
  },
  MuiTooltip: {
    styleOverrides: {
      tooltip: {
        fontSize: '0.75rem',
        fontWeight: 500,
      },
    },
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// Dark theme
// ─────────────────────────────────────────────────────────────────────────────
export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main:  'hsl(188, 80%, 42%)',
      light: 'hsl(188, 80%, 55%)',
      dark:  'hsl(188, 80%, 30%)',
      contrastText: '#000',
    },
    secondary: { main: '#a855f7' },
    error:   { main: '#ef4444' },
    warning: { main: '#f97316' },
    success: { main: '#22c55e' },
    info:    { main: '#3b82f6' },
    background: {
      default: 'hsl(222, 20%, 8%)',
      paper:   'hsl(222, 18%, 11%)',
    },
    text: {
      primary:   'hsl(210, 20%, 88%)',
      secondary: 'hsl(210, 10%, 52%)',
      disabled:  'hsl(210, 10%, 35%)',
    },
    divider: 'hsl(222, 14%, 18%)',
    action: {
      hover:    'rgba(255,255,255,0.05)',
      selected: 'rgba(14,165,180,0.12)',
      disabled: 'rgba(255,255,255,0.12)',
    },
  },
  typography: sharedTypography,
  shape: sharedShape,
  components: sharedComponents('dark'),
});

// ─────────────────────────────────────────────────────────────────────────────
// Light theme — same hues, flipped lightness
// ─────────────────────────────────────────────────────────────────────────────
export const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main:  'hsl(188, 80%, 36%)',
      light: 'hsl(188, 80%, 48%)',
      dark:  'hsl(188, 80%, 26%)',
      contrastText: '#fff',
    },
    secondary: { main: '#9333ea' },
    error:   { main: '#dc2626' },
    warning: { main: '#ea580c' },
    success: { main: '#16a34a' },
    info:    { main: '#2563eb' },
    background: {
      default: 'hsl(222, 20%, 95%)',
      paper:   '#ffffff',
    },
    text: {
      primary:   'hsl(222, 20%, 12%)',
      secondary: 'hsl(222, 12%, 42%)',
      disabled:  'hsl(222, 12%, 65%)',
    },
    divider: 'hsl(222, 14%, 86%)',
    action: {
      hover:    'rgba(0,0,0,0.04)',
      selected: 'rgba(14,165,180,0.10)',
      disabled: 'rgba(0,0,0,0.12)',
    },
  },
  typography: sharedTypography,
  shape: sharedShape,
  components: sharedComponents('light'),
});

export default darkTheme;
