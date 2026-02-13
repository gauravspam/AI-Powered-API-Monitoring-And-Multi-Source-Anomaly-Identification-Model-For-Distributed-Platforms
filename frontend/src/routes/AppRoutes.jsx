import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Login from '../pages/Login';
import Dashboard from '../pages/Dashboard';
import MLSimulator from '../pages/MLSimulator';

const AppRoutes = () => {
    return (
        <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<Dashboard />} />
            <Route path="/simulator" element={<MLSimulator />} />
        </Routes>
    );
};

export default AppRoutes;
