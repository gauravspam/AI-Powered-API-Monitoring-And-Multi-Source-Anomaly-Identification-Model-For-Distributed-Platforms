import { Routes, Route } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';
import Dashboard from '@/pages/Dashboard';
import Services from '@/pages/Services';
import Alerts from '@/pages/Alerts';
import Logs from '@/pages/Logs';
import Models from '@/pages/Models';
import Settings from '@/pages/Settings';
import NotFound from '@/pages/NotFound';

export const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="services" element={<Services />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="logs" element={<Logs />} />
        <Route path="models" element={<Models />} />
        <Route path="settings" element={<Settings />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
};
