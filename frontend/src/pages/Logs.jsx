import { useState, useMemo, useEffect, useRef, useCallback } from 'react';
import { unwrapArray } from '../utils/dataUtils'; // Import the fix
import {
    Container,
    Typography,
    Box,
    Paper,
    Grid,
    TextField,
    ToggleButtonGroup,
    ToggleButton,
    Card,
    CardContent,
    IconButton,
    Tooltip,
} from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';
import EnvironmentFilter from '@/components/EnvironmentFilter';
import LogTimeline from '@/components/LogTimeline';
import api from '@/api/http';
// import { logEvents as mockEvents } from '@/data/mockLogs'; // Removed mock usage

const Logs = () => {
    const [logEvents, setLogEvents] = useState([]);
    const [loading, setLoading] = useState(false);
    const [filter, setFilter] = useState('ALL');
    const [searchQuery, setSearchQuery] = useState('');
    const [viewMode, setViewMode] = useState('list');
    const [autoRefresh, setAutoRefresh] = useState(false);

    // Fetch logs from API
    const fetchLogs = useCallback(async () => {
        setLoading(true);
        try {
            const res = await api.get('/logs'); // Adjust endpoint if needed
            // FIX: Safely unwrap the response data
            const cleanLogs = unwrapArray(res.data, ['content', 'data', 'events']);
            setLogEvents(cleanLogs);
        } catch (error) {
            console.error('Failed to fetch logs:', error);
            // Fallback to empty array on error prevents map() crashes
            setLogEvents([]);
        } finally {
            setLoading(false);
        }
    }, []);

    // Initial load & Auto-refresh logic
    useEffect(() => {
        fetchLogs();
        let interval;
        if (autoRefresh) {
            interval = setInterval(fetchLogs, 5000);
        }
        return () => clearInterval(interval);
    }, [autoRefresh, fetchLogs]);

    // Filtering logic
    const filteredLogs = useMemo(() => {
        // Defensive: ensure logEvents is always an array before filtering
        const safeEvents = Array.isArray(logEvents) ? logEvents : [];

        return safeEvents.filter((log) => {
            const matchesEnv = filter === 'ALL' || (log.environment && log.environment.toUpperCase() === filter);
            const matchesSearch =
                !searchQuery ||
                (log.message && log.message.toLowerCase().includes(searchQuery.toLowerCase())) ||
                (log.serviceName && log.serviceName.toLowerCase().includes(searchQuery.toLowerCase()));
            return matchesEnv && matchesSearch;
        });
    }, [logEvents, filter, searchQuery]);

    const handleRefresh = () => {
        fetchLogs();
    };

    return (
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h4" component="h1" gutterBottom>
                    System Logs
                </Typography>
                <Box>
                    <Tooltip title="Auto Refresh">
                        <ToggleButton
                            value="check"
                            selected={autoRefresh}
                            onChange={() => setAutoRefresh(!autoRefresh)}
                            sx={{ mr: 1 }}
                        >
                            <RefreshIcon />
                        </ToggleButton>
                    </Tooltip>
                </Box>
            </Box>

            {/* Filters Section */}
            <Paper sx={{ p: 2, mb: 3 }}>
                <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} md={6}>
                        <TextField
                            fullWidth
                            label="Search Logs"
                            variant="outlined"
                            size="small"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <EnvironmentFilter value={filter} onChange={setFilter} />
                    </Grid>
                </Grid>
            </Paper>

            {/* Logs Display Section */}
            <Paper sx={{ p: 2, minHeight: '500px' }}>
                {loading && logEvents.length === 0 ? (
                    <Typography sx={{ p: 2 }}>Loading logs...</Typography>
                ) : (
                    <LogTimeline events={filteredLogs} />
                )}
            </Paper>
        </Container>
    );
};

export default Logs;
