import { useEffect, useState } from 'react'
import viteLogo from '/vite.svg'

function App() {
  const [health, setHealth] = useState(null)
  
  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL}/api/v1/dashboard/health`)
      .then(r => r.json())
      .then(setHealth)
  }, [])

  return (
    <div>
      <a href="https://vitejs.dev">
        <img src={viteLogo} alt="Vite logo" />
      </a>
      <h1>API Monitoring Dashboard</h1>
      <p>Backend Health: {health?.status || 'Loading...'}</p>
      <button onClick={() => fetch(`${import.meta.env.VITE_API_URL}/api/v1/dashboard/test-anomaly`, {method: 'POST'})}>
        Generate Test Anomaly
      </button>
    </div>
  )
}

export default App


// import { createContext, useState, useMemo } from 'react';
// import { BrowserRouter } from 'react-router-dom';
// import { ThemeProvider, CssBaseline } from '@mui/material';
// import { AppRoutes } from '@/routes/AppRoutes.jsx';
// import { createTheme } from '@mui/material/styles';

// export const ThemeContext = createContext({ toggleTheme: () => { } });


// function App() {
//   const [mode, setMode] = useState('dark');
//   const getTheme = (mode) => createTheme({
//     palette: {
//       mode:mode
//     }
//   });
//   // useMemo's first argument should be a function, and getTheme expects mode
//   const theme = useMemo(() => getTheme(mode), [mode]);

//   const toggleTheme = () => {
//     setMode((prevMode) => (prevMode === 'light' ? 'dark' : 'light'));
//   };

//   return (
//     <ThemeContext.Provider value={{ toggleTheme }}>
//       <ThemeProvider theme={theme}>
//         <CssBaseline />
//         <BrowserRouter>
//           <AppRoutes />
//         </BrowserRouter>
//       </ThemeProvider>
//     </ThemeContext.Provider >
//   );
// }

// export default App;
