import React, { useState, useEffect } from 'react';
import { Container, Typography, Grid, Paper, Box, CircularProgress } from '@mui/material';
import { StatusChip } from '../components/StatusChip';
import api from '../api/http';

const Services = () => {
    const [services, setServices] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadServices = async () => {
            try {
                // Fetch traces to deduce active services
                const response = await api.get('/traces/recent?limit=50');
                const traces = response.data || [];

                // Group by serviceName
                const serviceMap = new Map();
                traces.forEach(t => {
                    if (!serviceMap.has(t.serviceName)) {
                        serviceMap.set(t.serviceName, {
                            name: t.serviceName,
                            status: 'healthy',
                            lastSeen: t.timestamp
                        });
                    }
                });
                setServices(Array.from(serviceMap.values()));
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        loadServices();
    }, []);

    return (
        <Container maxWidth="xl">
            <Typography variant="h4" fontWeight="bold" sx={{ mb: 3 }}>Monitored Services</Typography>
            {loading ? <CircularProgress /> : (
                <Grid container spacing={3}>
                    {services.map(service => (
                        <Grid item xs={12} md={4} key={service.name}>
                            <Paper sx={{ p: 3 }}>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <Typography variant="h6">{service.name}</Typography>
                                    <StatusChip value={service.status} type="status" />
                                </Box>
                                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                    Last Active: {new Date(service.lastSeen).toLocaleString()}
                                </Typography>
                            </Paper>
                        </Grid>
                    ))}
                </Grid>
            )}
        </Container>
    );
};

export default Services;
