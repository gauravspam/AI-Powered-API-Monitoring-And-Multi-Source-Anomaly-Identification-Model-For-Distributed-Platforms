import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
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
let cachedDashboard = {
  kpiCards: null,
  environmentSummary: null,
  recentAnomalies: null,
  trafficSeries: null,
  timestamp: null,
};

// Pre-fetch data as soon as module loads
let initialFetchPromise = null;
let prefetchFailed = false;

const THROTTLE_MS = 5000;
const POLL_INTERVAL_MS = 30000;

const prefetchData = () => {
  if (!initialFetchPromise && !cachedDashboard.kpiCards) {
    initialFetchPromise = Promise.all([
      api.get('/dashboard/kpi').catch(() => ({ data: [] })),
      api.get('/dashboard/env-summary').catch(() => ({ data: [] })),
      api.get('/dashboard/anomalies').catch(() => ({ data: [] })),
      api.get('/dashboard/traffic').catch(() => ({ data: [] })),
    ]).then(([kpiRes, envRes, anomaliesRes, trafficRes]) => {
      const kpiData = (kpiRes.data || []).map((card) => ({
        ...card,
        icon: iconMap[card.label] || SpeedIcon,
      }));
      const envData = envRes.data || [];
      const anomaliesData = anomaliesRes.data || [];
      const trafficData = trafficRes.data || [];

      // Check if we got actual data
      if (
        kpiData.length === 0 &&
        envData.length === 0 &&
        anomaliesData.length === 0 &&
        trafficData.length === 0
      ) {
        prefetchFailed = true;
      }

      const data = {
        kpiCards: kpiData,
        environmentSummary: envData,
        recentAnomalies: anomaliesData,
        trafficSeries: trafficData,
        timestamp: Date.now(),
      };
      cachedDashboard = data;
      return data;
    }).catch(() => {
      prefetchFailed = true;
      return {
        kpiCards: [],
        environmentSummary: [],
        recentAnomalies: [],
        trafficSeries: [],
        timestamp: Date.now(),
      };
    });
  }
  return initialFetchPromise;
};

// Start prefetch immediately on module load
prefetchData();

export const Dashboard = () => {
  const [selectedEnv, setSelectedEnv] = useState('All');
  const [selectedSeverity, setSelectedSeverity] = useState('All');
  const [refreshing, setRefreshing] = useState(false);
  
  // Initialize state from cache
  const [kpiCards, setKpiCards] = useState(cachedDashboard.kpiCards || []);
  const [environmentSummary, setEnvironmentSummary] = useState(cachedDashboard.environmentSummary || []);
  const [recentAnomalies, setRecentAnomalies] = useState(cachedDashboard.recentAnomalies || []);
  const [trafficSeries, setTrafficSeries] = useState(cachedDashboard.trafficSeries || []);

  // Refs for lifecycle management
  const isMountedRef = useRef(true);
  const pollIntervalRef = useRef(null);
  const lastFetchTime = useRef(cachedDashboard.timestamp || 0);

  // Smart update detection using length checks
  const shouldUpdate = useCallback((cachedData, newData) => {
    if (!Array.isArray(cachedData) || !Array.isArray(newData)) return true;
    return cachedData.length !== newData.length;
  }, []);

  // Fetch with throttling
  const fetchDashboardData = useCallback(async (isPolling = false) => {
    try {
      // Throttle: Don't fetch if last fetch was less than 5 seconds ago (unless manual refresh)
      if (isPolling && Date.now() - lastFetchTime.current < THROTTLE_MS) {
        return;
      }

      const [kpiRes, envRes, anomaliesRes, trafficRes] = await Promise.all([
        api.get('/dashboard/kpi').catch(() => ({ data: [] })),
        api.get('/dashboard/env-summary').catch(() => ({ data: [] })),
        api.get('/dashboard/anomalies').catch(() => ({ data: [] })),
        api.get('/dashboard/traffic').catch(() => ({ data: [] })),
      ]);

      if (!isMountedRef.current) return;

      lastFetchTime.current = Date.now();

      const newKpiData = (kpiRes.data || []).map((card) => ({
        ...card,
        icon: iconMap[card.label] || SpeedIcon,
      }));
      const newEnvData = envRes.data || [];
      const newAnomaliesData = anomaliesRes.data || [];
      const newTrafficData = trafficRes.data || [];

      // Fast shallow comparison - only update if lengths differ
      const kpiChanged = shouldUpdate(kpiCards, newKpiData);
      const envChanged = shouldUpdate(environmentSummary, newEnvData);
      const anomaliesChanged = shouldUpdate(recentAnomalies, newAnomaliesData);
      const trafficChanged = shouldUpdate(trafficSeries, newTrafficData);

      if (kpiChanged || envChanged || anomaliesChanged || trafficChanged || !isPolling) {
        // Batch state updates
        if (kpiChanged) setKpiCards(newKpiData);
        if (envChanged) setEnvironmentSummary(newEnvData);
        if (anomaliesChanged) setRecentAnomalies(newAnomaliesData);
        if (trafficChanged) setTrafficSeries(newTrafficData);

        cachedDashboard = {
          kpiCards: newKpiData,
          environmentSummary: newEnvData,
          recentAnomalies: newAnomaliesData,
          trafficSeries: newTrafficData,
          timestamp: Date.now(),
        };

        if (isPolling && (kpiChanged || envChanged || anomaliesChanged || trafficChanged)) {
          console.log('Dashboard updated with new data');
        }
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    }
  }, [kpiCards, environmentSummary, recentAnomalies, trafficSeries, shouldUpdate]);

  const startPolling = useCallback(() => {
    if (!pollIntervalRef.current) {
      pollIntervalRef.current = setInterval(() => {
        fetchDashboardData(true);
      }, POLL_INTERVAL_MS);
    }
  }, [fetchDashboardData]);

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  }, []);

  // Component mount and initial data loading
  useEffect(() => {
    isMountedRef.current = true;

    const loadData = async () => {
      // If prefetch failed or returned empty data, retry
      if (
        prefetchFailed ||
        (cachedDashboard.kpiCards && cachedDashboard.kpiCards.length === 0)
      ) {
        // Reset flags
        initialFetchPromise = null;
        prefetchFailed = false;
        await fetchDashboardData(false);
      } else if (initialFetchPromise) {
        // Use prefetched data if available
        try {
          const data = await initialFetchPromise;
          if (isMountedRef.current && data) {
            setKpiCards(data.kpiCards);
            setEnvironmentSummary(data.environmentSummary);
            setRecentAnomalies(data.recentAnomalies);
            setTrafficSeries(data.trafficSeries);
          }
        } catch (err) {
          // If prefetch failed, try again
          await fetchDashboardData(false);
        }
      } else {
        // No prefetch, fetch normally
        await fetchDashboardData(false);
      }
    };

    loadData();
    startPolling();

    return () => {
      isMountedRef.current = false;
      stopPolling();
    };
  }, [fetchDashboardData, startPolling, stopPolling]);

  // Manual refresh handler
  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    lastFetchTime.current = 0; // Reset throttle to allow immediate fetch
    fetchDashboardData(false).finally(() => {
      if (isMountedRef.current) {
        setRefreshing(false);
      }
    });
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