import { createContext, useState, useMemo } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { getTheme } from '@/theme';
import { AppRoutes } from '@/routes/AppRoutes.jsx';

export const ThemeContext = createContext({ toggleTheme: () => {} });

function App() {
  const [mode, setMode] = useState('light');

  const theme = useMemo(() => getTheme(mode), [mode]);

  const toggleTheme = () => {
    setMode((prevMode) => (prevMode === 'light' ? 'dark' : 'light'));
  };

  return (
    <ThemeContext.Provider value={{ toggleTheme }}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </ThemeProvider>
    </ThemeContext.Provider>
  );
}

export default App;
