import { BrowserRouter, Routes, Route } from "react-router-dom";
import MainLayout from "./componets/MainLayout";

import Dashboard from "./pages/Dashboard";
import APIs from "./pages/APIs";
import APIDetail from "./pages/APIDetail";
import Anomalies from "./pages/Anomalies";
import Predictions from "./pages/Predictions";
import Alerts from "./pages/Alerts";
import Logs from "./pages/Logs";
import SystemHealth from "./pages/SystemHealth";

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/apis" element={<APIs />} />
          <Route path="/apis/:apiId" element={<APIDetail />} />
          <Route path="/anomalies" element={<Anomalies />} />
          <Route path="/predictions" element={<Predictions />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/system-health" element={<SystemHealth />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
