import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppThemeProvider } from './context/ThemeContext';
import MainLayout from './layouts/MainLayout';
import Dashboard from './pages/Dashboard';
import Services from './pages/Services';
import Alerts from './pages/Alerts';
import Logs from './pages/Logs';
import Traces from './pages/Traces';
import Models from './pages/Models';
import Simulator from './pages/Simulator';
import NotFound from './pages/NotFound';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppThemeProvider>
        <BrowserRouter>
          <MainLayout>
            <Routes>
              <Route path="/"          element={<Dashboard />} />
              <Route path="/services"  element={<Services />} />
              <Route path="/alerts"    element={<Alerts />} />
              <Route path="/logs"      element={<Logs />} />
              <Route path="/traces"    element={<Traces />} />
              <Route path="/models"    element={<Models />} />
              <Route path="/simulator" element={<Simulator />} />
              <Route path="*"          element={<NotFound />} />
            </Routes>
          </MainLayout>
        </BrowserRouter>
      </AppThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
