import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Container,
  Grid,
  Typography,
  Box,
  Paper,
  List,
  ListItem,
  Divider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Speed as SpeedIcon,
  ErrorOutline as ErrorIcon,
  Warning as WarningIcon,
  Timer as TimerIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import StatCard from '@/components/StatCard';
import AnomalyTable from '@/components/AnomalyTable';
import MetricChart from '@/components/MetricChart';
import EnvironmentFilter from '@/components/EnvironmentFilter';
import StatusChip from '@/components/StatusChip';
import api from '@/api/http';

// Icon mapping for KPI cards
const iconMap = {
  "Total Requests": SpeedIcon,
  "Error Rate": ErrorIcon,
  "Anomaly Rate": WarningIcon,
  "Avg Latency": TimerIcon,
};

// Module-level cache that persists across navigation
const cache = {
  kpiCards: [],
  environmentSummary: [],
  recentAnomalies: [],
  trafficSeries: [],
  lastFetch: 0,
  prefetchStarted: false,
};

// Request throttling config
const THROTTLE_MS = 5000;
const POLL_INTERVAL_MS = 30000;

// Prefetch data on module load
const prefetchData = async () => {
  if (cache.prefetchStarted) return;
  cache.prefetchStarted = true;

  try {
    const [kpiRes, envRes, anomaliesRes, trafficRes] = await Promise.allSettled([
      api.get('/dashboard/kpi'),
      api.get('/dashboard/env-summary'),
      api.get('/dashboard/anomalies'),
      api.get('/dashboard/traffic'),
    ]);

    if (kpiRes.status === 'fulfilled' && kpiRes.value?.data) {
      cache.kpiCards = kpiRes.value.data.map((card) => ({
        ...card,
        icon: iconMap[card.label] || SpeedIcon,
      }));
    }

    if (envRes.status === 'fulfilled' && envRes.value?.data) {
      cache.environmentSummary = envRes.value.data;
    }

    if (anomaliesRes.status === 'fulfilled' && anomaliesRes.value?.data) {
      cache.recentAnomalies = anomaliesRes.value.data;
    }

    if (trafficRes.status === 'fulfilled' && trafficRes.value?.data) {
      cache.trafficSeries = trafficRes.value.data;
    }

    cache.lastFetch = Date.now();
  } catch (error) {
    console.error('Prefetch error:', error);
  }
};

// Start prefetch immediately on module load
prefetchData();

export const Dashboard = () => {
  const [selectedEnv, setSelectedEnv] = useState('All');
  const [selectedSeverity, setSelectedSeverity] = useState('All');
  const [refreshing, setRefreshing] = useState(false);

  // Initialize from cache immediately
  const [kpiCards, setKpiCards] = useState(cache.kpiCards);
  const [environmentSummary, setEnvironmentSummary] = useState(cache.environmentSummary);
  const [recentAnomalies, setRecentAnomalies] = useState(cache.recentAnomalies);
  const [trafficSeries, setTrafficSeries] = useState(cache.trafficSeries);

  // Smart update detection using length checks
  const shouldUpdate = useCallback((cachedData, newData) => {
    if (!Array.isArray(cachedData) || !Array.isArray(newData)) return true;
    return cachedData.length !== newData.length;
  }, []);

  // Fetch with throttling and auto-retry
  const fetchDashboardData = useCallback(async (bypassThrottle = false) => {
    const now = Date.now();
    
    // Throttle check
    if (!bypassThrottle && now - cache.lastFetch < THROTTLE_MS) {
      return;
    }

    if (bypassThrottle) {
      setRefreshing(true);
    }

    try {
      const [kpiRes, envRes, anomaliesRes, trafficRes] = await Promise.allSettled([
        api.get('/dashboard/kpi'),
        api.get('/dashboard/env-summary'),
        api.get('/dashboard/anomalies'),
        api.get('/dashboard/traffic'),
      ]);

      // Update KPI data if changed
      if (kpiRes.status === 'fulfilled' && kpiRes.value?.data) {
        const newKpiData = kpiRes.value.data.map((card) => ({
          ...card,
          icon: iconMap[card.label] || SpeedIcon,
        }));
        if (shouldUpdate(cache.kpiCards, newKpiData)) {
          cache.kpiCards = newKpiData;
          setKpiCards(newKpiData);
        }
      }

      // Update environment summary if changed
      if (envRes.status === 'fulfilled' && envRes.value?.data) {
        if (shouldUpdate(cache.environmentSummary, envRes.value.data)) {
          cache.environmentSummary = envRes.value.data;
          setEnvironmentSummary(envRes.value.data);
        }
      }

      // Update anomalies if changed
      if (anomaliesRes.status === 'fulfilled' && anomaliesRes.value?.data) {
        if (shouldUpdate(cache.recentAnomalies, anomaliesRes.value.data)) {
          cache.recentAnomalies = anomaliesRes.value.data;
          setRecentAnomalies(anomaliesRes.value.data);
        }
      }

      // Update traffic data if changed
      if (trafficRes.status === 'fulfilled' && trafficRes.value?.data) {
        if (shouldUpdate(cache.trafficSeries, trafficRes.value.data)) {
          cache.trafficSeries = trafficRes.value.data;
          setTrafficSeries(trafficRes.value.data);
        }
      }

      cache.lastFetch = now;
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      
      // Auto-retry on server restart (connection errors)
      if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
        setTimeout(() => fetchDashboardData(false), 5000);
      }
    } finally {
      if (bypassThrottle) {
        setRefreshing(false);
      }
    }
  }, [shouldUpdate]);

  // Initial fetch and polling
  useEffect(() => {
    // Fetch immediately if cache is stale
    const now = Date.now();
    if (now - cache.lastFetch >= THROTTLE_MS) {
      fetchDashboardData(false);
    }

    // Background polling every 30s
    const pollInterval = setInterval(() => {
      fetchDashboardData(false);
    }, POLL_INTERVAL_MS);

    return () => clearInterval(pollInterval);
  }, [fetchDashboardData]);

  // Manual refresh handler
  const handleRefresh = useCallback(() => {
    fetchDashboardData(true);
  }, [fetchDashboardData]);

  // Filter anomalies based on environment and severity (memoized)
  const filteredAnomalies = useMemo(() => {
    let filtered = recentAnomalies;
    if (selectedEnv !== 'All') {
      filtered = filtered.filter((a) => a.environment === selectedEnv);
    }
    if (selectedSeverity !== 'All') {
      filtered = filtered.filter((a) => a.severity === selectedSeverity);
    }
    return filtered;
  }, [selectedEnv, selectedSeverity, recentAnomalies]);

  // Memoized handlers
  const handleEnvChange = useCallback((e) => setSelectedEnv(e.target.value), []);
  const handleSeverityChange = useCallback((e) => setSelectedSeverity(e.target.value), []);
  const handleRowClick = useCallback((params) => console.log(params.row), []);

  return (
    <Container maxWidth="xl">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Box>
          <Typography variant="h4" gutterBottom fontWeight="bold">
            Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            Real-time monitoring and anomaly detection across distributed platforms
          </Typography>
        </Box>
        <Tooltip title="Refresh data">
          <IconButton onClick={handleRefresh} disabled={refreshing}>
            <RefreshIcon sx={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
          </IconButton>
        </Tooltip>
      </Box>

      {/* KPI Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {kpiCards.map((card) => (
          <Grid item xs={12} sm={6} md={3} key={card.id}>
            <StatCard {...card} />
          </Grid>
        ))}
      </Grid>

      {/* Traffic Chart and Environment Summary */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <MetricChart
            data={trafficSeries}
            metricKey="requestsPerSec"
            title="Requests per Second"
            height={300}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Environment Health
            </Typography>
            <List dense>
              {environmentSummary.map((env) => (
                <Box key={env.id}>
                  <ListItem
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="body2" fontWeight="bold">
                        {env.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {env.requestPerMin.toLocaleString()} req/min
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                      <StatusChip value={env.status} type="status" />
                      <Typography variant="caption" color="text.secondary">
                        {env.uptime}%
                      </Typography>
                    </Box>
                  </ListItem>
                  <Divider />
                </Box>
              ))}
            </List>
          </Paper>
        </Grid>
      </Grid>

      {/* Recent Anomalies */}
      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Recent Anomalies</Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Severity</InputLabel>
              <Select
                value={selectedSeverity}
                label="Severity"
                onChange={handleSeverityChange}
              >
                <MenuItem value="All">All Severities</MenuItem>
                <MenuItem value="critical">Critical</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="low">Low</MenuItem>
              </Select>
            </FormControl>
            <EnvironmentFilter
              value={selectedEnv}
              onChange={handleEnvChange}
            />
          </Box>
        </Box>
        <AnomalyTable rows={filteredAnomalies} onRowClick={handleRowClick} />
      </Paper>
    </Container>
  );
};

export default Dashboard;