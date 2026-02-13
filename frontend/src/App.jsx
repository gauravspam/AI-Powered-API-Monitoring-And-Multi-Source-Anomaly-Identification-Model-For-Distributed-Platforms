import { createContext, useState, useMemo } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, CssBaseline, createTheme } from '@mui/material';
import AppRoutes from './routes/AppRoutes'; // Default import
import { AuthProvider } from './contexts/AuthContext'; // Check path alias @/ vs ./

export const ThemeContext = createContext({ toggleTheme: () => { } });

function App() {
    const [mode, setMode] = useState('dark');
    const theme = useMemo(() => createTheme({ palette: { mode } }), [mode]);
    const toggleTheme = () => setMode((prev) => (prev === 'light' ? 'dark' : 'light'));

    return (
        <ThemeContext.Provider value={{ toggleTheme }}>
            <ThemeProvider theme={theme}>
                <CssBaseline />
                <BrowserRouter> {/* Router must wrap everything */}
                    <AuthProvider>
                        <AppRoutes />
                    </AuthProvider>
                </BrowserRouter>
            </ThemeProvider>
        </ThemeContext.Provider>
    );
}

export default App;




// import { createContext, useState, useMemo } from 'react';
// import { BrowserRouter } from 'react-router-dom';
// import { ThemeProvider, CssBaseline, createTheme } from '@mui/material';
// import AppRoutes from './routes/AppRoutes';
// import { AuthProvider } from '@/contexts/AuthContext';


// export const ThemeContext = createContext({ toggleTheme: () => { } });

// function App() {
//     const [mode, setMode] = useState('dark');

//     // Use default MUI theme with mode
//     const theme = useMemo(
//         () =>
//             createTheme({
//                 palette: {
//                     mode,
//                 },
//             }),
//         [mode]
//     );

//     const toggleTheme = () => {
//         setMode((prevMode) => (prevMode === 'light' ? 'dark' : 'light'));
//     };

//     return (
//         <ThemeContext.Provider value={{ toggleTheme }}>
//             <ThemeProvider theme={theme}>
//                 <CssBaseline />
//                 <BrowserRouter>
//                     <AuthProvider>
//                         <AppRoutes />
//                     </AuthProvider>
//                 </BrowserRouter>
//             </ThemeProvider>
//         </ThemeContext.Provider>
//     );
// }

// export default App;
