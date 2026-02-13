import React, { useState, useEffect, useCallback } from 'react';
import { Container, Typography, Box, IconButton, Tooltip, Grid, Paper, CircularProgress } from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';
import { AlertList } from '../components/AlertList';
import api from '../api/http';

const Alerts = () => {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedAlert, setSelectedAlert] = useState(null);

    const fetchAlerts = useCallback(async () => {
        setLoading(true);
        try {
            // Map anomalies to alerts structure
            const response = await api.get('/anomalies/recent?limit=20');
            const mappedAlerts = response.data.map(a => ({
                id: a.id,
                title: `Anomaly in ${a.serviceName}`,
                description: a.details || "Detected anomaly based on multi-source metrics",
                severity: a.severity || (a.score > 0.8 ? 'critical' : 'high'),
                status: a.status || 'open',
                serviceName: a.serviceName,
                environment: a.environment,
                createdAt: a.detectedAt,
                source: 'ML Model'
            }));
            setAlerts(mappedAlerts);
        } catch (error) {
            console.error("Failed to fetch alerts", error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAlerts();
    }, [fetchAlerts]);

    const handleResolve = async (id) => {
        try {
            await api.post(`/anomalies/${id}/resolve`);
            fetchAlerts(); // Refresh list
        } catch (error) {
            console.error("Resolve failed", error);
        }
    };

    return (
        <Container maxWidth="xl">
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h4" fontWeight="bold">System Alerts</Typography>
                <Tooltip title="Refresh">
                    <IconButton onClick={fetchAlerts}><RefreshIcon /></IconButton>
                </Tooltip>
            </Box>

            {loading ? <CircularProgress /> : (
                <Grid container spacing={3}>
                    <Grid item xs={12} md={selectedAlert ? 8 : 12}>
                        <AlertList
                            alerts={alerts}
                            onSelect={setSelectedAlert}
                            onResolve={handleResolve}
                        />
                    </Grid>
                    {selectedAlert && (
                        <Grid item xs={12} md={4}>
                            <Paper sx={{ p: 2 }}>
                                <Typography variant="h6">Alert Details</Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                    {selectedAlert.description}
                                </Typography>
                                {/* Add more details as needed */}
                            </Paper>
                        </Grid>
                    )}
                </Grid>
            )}
        </Container>
    );
};

export default Alerts;
