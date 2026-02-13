import React, { useState, useEffect, useCallback } from 'react';
import { Container, Typography, Box, Paper, CircularProgress, TextField } from '@mui/material';
import { LogTimeline } from '../components/LogTimeline';
import api from '../api/http';

const Logs = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [search, setSearch] = useState("");

    const fetchLogs = useCallback(async () => {
        setLoading(true);
        try {
            const endpoint = search ? `/logs/search?query=${search}` : '/logs/recent?limit=50';
            const response = await api.get(endpoint);
            setLogs(response.data || []);
        } catch (error) {
            console.error("Failed to fetch logs", error);
        } finally {
            setLoading(false);
        }
    }, [search]);

    // Debounce search
    useEffect(() => {
        const timer = setTimeout(fetchLogs, 500);
        return () => clearTimeout(timer);
    }, [fetchLogs]);

    return (
        <Container maxWidth="xl">
            <Typography variant="h4" fontWeight="bold" sx={{ mb: 3 }}>System Logs</Typography>

            <Paper sx={{ p: 2, mb: 3 }}>
                <TextField
                    fullWidth
                    label="Search Logs (e.g. 'error', 'service-a')"
                    variant="outlined"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </Paper>

            {loading ? <CircularProgress /> : (
                <Paper sx={{ p: 2 }}>
                    {logs.length > 0 ? <LogTimeline events={logs} /> : <Typography>No logs found.</Typography>}
                </Paper>
            )}
        </Container>
    );
};

export default Logs;
