import React, { useState, useEffect } from 'react';
import { Grid, Box, Typography, Alert, CircularProgress } from '@mui/material';
import { Speed as SpeedIcon, Error as ErrorIcon, Warning as WarningIcon, Timer as TimerIcon } from '@mui/icons-material';
import StatCard from '../components/StatCard';
import EnvironmentFilter from '../components/EnvironmentFilter';
import MetricChart from '../components/MetricChart';
import AnomalyTable from '../components/AnomalyTable';
import api from '../api/http';

const Dashboard = () => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // State for dashboard data
    const [kpiCards, setKpiCards] = useState([]);
    const [environmentSummary, setEnvironmentSummary] = useState([]);
    const [recentAnomalies, setRecentAnomalies] = useState([]);
    const [trafficData, setTrafficData] = useState([]);

    const [selectedEnv, setSelectedEnv] = useState('All');

    const loadData = async () => {
        try {
            setLoading(true);
            // Fetch from real Spring endpoint
            const response = await api.get('/overview');
            const data = response.data;

            // Map Spring response to UI structure
            // Adjust these mappings based on exactly what your /api/overview returns
            setKpiCards([
                { id: 1, label: "Total Requests", value: data.totalRequests || "0", icon: <SpeedIcon /> },
                { id: 2, label: "Error Rate", value: data.errorRate || "0", unit: "%", icon: <ErrorIcon /> },
                { id: 3, label: "Anomalies", value: data.anomalyCount || "0", icon: <WarningIcon /> },
                { id: 4, label: "Avg Latency", value: data.avgLatency || "0", unit: "ms", icon: <TimerIcon /> }
            ]);

            setEnvironmentSummary(data.environments || []);
            setRecentAnomalies(data.recentAnomalies || []);

            // Transform traffic series if needed
            const traffic = data.trafficSeries || [];
            setTrafficData(traffic.map(t => ({ timestamp: new Date(t.time), value: t.value })));

        } catch (err) {
            console.error("Dashboard load failed", err);
            setError("Failed to load dashboard data. Ensure backend is running.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    if (loading && kpiCards.length === 0) {
        return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>;
    }

    return (
        <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h4" fontWeight="bold">System Overview</Typography>
                <EnvironmentFilter value={selectedEnv} onChange={(e) => setSelectedEnv(e.target.value)} />
            </Box>

            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

            {/* KPI Cards */}
            <Grid container spacing={3} mb={4}>
                {kpiCards.map((card) => (
                    <Grid item xs={12} sm={6} md={3} key={card.id}>
                        <StatCard
                            label={card.label}
                            value={card.value}
                            unit={card.unit}
                            icon={card.icon}
                        />
                    </Grid>
                ))}
            </Grid>

            {/* Charts & Tables */}
            <Grid container spacing={3}>
                <Grid item xs={12} lg={8}>
                    <MetricChart
                        title="Traffic Overview"
                        data={trafficData}
                        metricKey="value"
                        height={350}
                    />
                </Grid>
                <Grid item xs={12} lg={4}>
                    {/* Environment Summary or other widgets can go here */}
                    <Alert severity="info">Environment summary widget placeholder</Alert>
                </Grid>

                <Grid item xs={12}>
                    <Box sx={{ mt: 2 }}>
                        <Typography variant="h6" gutterBottom>Recent Anomalies</Typography>
                        <AnomalyTable rows={recentAnomalies} />
                    </Box>
                </Grid>
            </Grid>
        </Box>
    );
};

export default Dashboard;
