import { createContext, useState, useMemo } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { AppRoutes } from '@/routes/AppRoutes.jsx';
import { createTheme } from '@mui/material/styles';

export const ThemeContext = createContext({ toggleTheme: () => { } });


function App() {
  const [mode, setMode] = useState('dark');
  const getTheme = (mode) => createTheme({
    palette: {
      mode:mode
    }
  });
  // useMemo's first argument should be a function, and getTheme expects mode
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
    </ThemeContext.Provider >
  );
}

export default App;
