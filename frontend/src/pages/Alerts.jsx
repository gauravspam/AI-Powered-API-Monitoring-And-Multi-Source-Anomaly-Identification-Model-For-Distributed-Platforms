import { useState, useMemo, useEffect, useRef, useCallback } from 'react';
import {
  Container,
  Typography,
  Box,
  ToggleButtonGroup,
  ToggleButton,
  Paper,
  Grid,
  IconButton,
  Tooltip,
} from '@mui/material';
import { Refresh } from '@mui/icons-material';
import AlertList from '@/components/AlertList';
import EnvironmentFilter from '@/components/EnvironmentFilter';
import api from '@/api/http';

// Module-level cache that persists across component mounts/unmounts
const cache = {
  alerts: [],
  logEvents: [],
  lastFetchTime: 0,
  isInitialized: false,
};

// Module-level fetching state to prevent duplicate requests
let isFetching = false;
let fetchPromise = null;
let pollingInterval = null;

// Start prefetching immediately when module loads (before component mounts)
const prefetchData = async () => {
  if (isFetching || cache.isInitialized) return fetchPromise;

  isFetching = true;
  fetchPromise = Promise.all([
    api.get('/alerts').catch(() => ({ data: [] })),
    api.get('/logs/events').catch(() => ({ data: [] })),
  ])
    .then(([alertsRes, logsRes]) => {
      const newAlerts = alertsRes.data || [];
      const newLogs = logsRes.data || [];

      cache.alerts = newAlerts;
      cache.logEvents = newLogs;
      cache.lastFetchTime = Date.now();
      cache.isInitialized = true;

      return { alerts: newAlerts, logs: newLogs };
    })
    .catch((error) => {
      console.error('Prefetch error:', error);
      cache.isInitialized = true; // Mark as initialized even on error
      return { alerts: [], logs: [] };
    })
    .finally(() => {
      isFetching = false;
      fetchPromise = null;
    });

  return fetchPromise;
};

// Start prefetching immediately
prefetchData();

const POLL_INTERVAL = 30000; // 30 seconds
const THROTTLE_WINDOW = 5000; // 5 seconds

export const Alerts = () => {
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [selectedEnv, setSelectedEnv] = useState('All');
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [alerts, setAlerts] = useState(cache.alerts);
  const [logEvents, setLogEvents] = useState(cache.logEvents);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  const mountedRef = useRef(true);
  const updateTimeoutRef = useRef(null);

  // Fetch data with throttling and change detection
  const fetchData = useCallback(async (forceRefresh = false) => {
    if (!mountedRef.current) return;

    const now = Date.now();
    const timeSinceLastFetch = now - cache.lastFetchTime;

    // Throttle requests (unless force refresh or server restart scenario)
    if (!forceRefresh && timeSinceLastFetch < THROTTLE_WINDOW && cache.isInitialized) {
      return;
    }

    // If already fetching, wait for that request
    if (isFetching && fetchPromise) {
      try {
        const result = await fetchPromise;
        if (mountedRef.current) {
          setAlerts(result.alerts);
          setLogEvents(result.logs);
        }
      } catch (error) {
        console.error('Error waiting for fetch:', error);
      }
      return;
    }

    isFetching = true;
    if (forceRefresh) setIsRefreshing(true);

    try {
      const [alertsRes, logsRes] = await Promise.all([
        api.get('/alerts').catch(() => ({ data: [] })),
        api.get('/logs/events').catch(() => ({ data: [] })),
      ]);

      const newAlerts = alertsRes.data || [];
      const newLogs = logsRes.data || [];

      // Fast length-based change detection
      const alertsChanged = newAlerts.length !== cache.alerts.length;
      const logsChanged = newLogs.length !== cache.logEvents.length;
      const hasData = newAlerts.length > 0 || newLogs.length > 0;
      const cacheWasEmpty = cache.alerts.length === 0 && cache.logEvents.length === 0;

      // Update if: data changed, cache was empty and now has data, or server restart detected
      if (alertsChanged || logsChanged || (cacheWasEmpty && hasData)) {
        cache.alerts = newAlerts;
        cache.logEvents = newLogs;
        cache.lastFetchTime = now;

        if (mountedRef.current) {
          // Batch state updates
          setAlerts(newAlerts);
          setLogEvents(newLogs);
        }
      } else {
        // No changes, just update timestamp
        cache.lastFetchTime = now;
      }

      cache.isInitialized = true;
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      isFetching = false;
      fetchPromise = null;
      if (forceRefresh && mountedRef.current) {
        setIsRefreshing(false);
      }
    }
  }, []);

  // Manual refresh handler
  const handleRefresh = useCallback(() => {
    fetchData(true);
  }, [fetchData]);

  // Initial load and polling setup
  useEffect(() => {
    mountedRef.current = true;

    // If cache is already populated, use it immediately
    if (cache.isInitialized && cache.alerts.length > 0) {
      setAlerts(cache.alerts);
      setLogEvents(cache.logEvents);
    }

    // Initial fetch (will be throttled if prefetch succeeded)
    fetchData();

    // Set up polling interval
    pollingInterval = setInterval(() => {
      fetchData();
    }, POLL_INTERVAL);

    // Cleanup on unmount
    return () => {
      mountedRef.current = false;
      if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
      }
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
      }
    };
  }, [fetchData]);

  // Fast-path filtering with skip optimization
  const filteredAlerts = useMemo(() => {
    // Fast path: if all filters are default, return all alerts
    if (selectedSeverity === 'all' && selectedStatus === 'all' && selectedEnv === 'All') {
      return alerts;
    }

    // Apply filters
    return alerts.filter((alert) => {
      if (selectedSeverity !== 'all' && alert.severity !== selectedSeverity) return false;
      if (selectedStatus !== 'all' && alert.status !== selectedStatus) return false;
      if (selectedEnv !== 'All' && alert.environment !== selectedEnv) return false;
      return true;
    });
  }, [selectedSeverity, selectedStatus, selectedEnv, alerts]);

  const handleAcknowledge = useCallback(async (alertId) => {
    try {
      await api.post(`/api/alerts/${alertId}/acknowledge`).catch(() => {
        console.log('Acknowledge API not available, updating locally');
      });

      const now = new Date().toISOString();
      const updatedAlerts = alerts.map(alert =>
        alert.id === alertId 
          ? { ...alert, status: 'acknowledged', lastUpdatedAt: now } 
          : alert
      );
      
      // Update both state and cache
      setAlerts(updatedAlerts);
      cache.alerts = updatedAlerts;

      // Update selected alert if needed
      setSelectedAlert(prev => 
        prev?.id === alertId 
          ? { ...prev, status: 'acknowledged', lastUpdatedAt: now }
          : prev
      );
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  }, [alerts]);

  const handleResolve = useCallback(async (alertId) => {
    try {
      await api.post(`/api/alerts/${alertId}/resolve`).catch(() => {
        console.log('Resolve API not available, updating locally');
      });

      const now = new Date().toISOString();
      const updatedAlerts = alerts.map(alert =>
        alert.id === alertId 
          ? { ...alert, status: 'resolved', lastUpdatedAt: now } 
          : alert
      );
      
      // Update both state and cache
      setAlerts(updatedAlerts);
      cache.alerts = updatedAlerts;

      // Update selected alert if needed
      setSelectedAlert(prev => 
        prev?.id === alertId 
          ? { ...prev, status: 'resolved', lastUpdatedAt: now }
          : prev
      );
    } catch (error) {
      console.error('Error resolving alert:', error);
    }
  }, [alerts]);

  const relatedLogs = useMemo(() => {
    if (!selectedAlert) return [];
    return logEvents
      .filter((log) => log.serviceName === selectedAlert.serviceName)
      .slice(0, 5);
  }, [selectedAlert, logEvents]);

  return (
    <Container maxWidth="xl">
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Box>
          <Typography variant="h4" gutterBottom fontWeight="bold">
            Alerts
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            Manage and respond to system alerts and anomalies
          </Typography>
        </Box>
        <Tooltip title="Refresh data">
          <IconButton 
            onClick={handleRefresh} 
            disabled={isRefreshing}
            sx={{ 
              animation: isRefreshing ? 'spin 1s linear infinite' : 'none',
              '@keyframes spin': {
                '0%': { transform: 'rotate(0deg)' },
                '100%': { transform: 'rotate(360deg)' },
              },
            }}
          >
            <Refresh />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Filters */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Box>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Severity
          </Typography>
          <ToggleButtonGroup
            value={selectedSeverity}
            exclusive
            onChange={(e, val) => val && setSelectedSeverity(val)}
            size="small"
          >
            <ToggleButton value="all">All</ToggleButton>
            <ToggleButton value="critical">Critical</ToggleButton>
            <ToggleButton value="high">High</ToggleButton>
            <ToggleButton value="medium">Medium</ToggleButton>
            <ToggleButton value="low">Low</ToggleButton>
          </ToggleButtonGroup>
        </Box>

        <Box>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Status
          </Typography>
          <ToggleButtonGroup
            value={selectedStatus}
            exclusive
            onChange={(e, val) => val && setSelectedStatus(val)}
            size="small"
          >
            <ToggleButton value="all">All</ToggleButton>
            <ToggleButton value="open">Open</ToggleButton>
            <ToggleButton value="acknowledged">Acknowledged</ToggleButton>
            <ToggleButton value="resolved">Resolved</ToggleButton>
          </ToggleButtonGroup>
        </Box>

        <Box>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Environment
          </Typography>
          <EnvironmentFilter
            value={selectedEnv}
            onChange={(e) => setSelectedEnv(e.target.value)}
          />
        </Box>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={selectedAlert ? 8 : 12}>
          <AlertList
            alerts={filteredAlerts}
            onSelect={setSelectedAlert}
            onAcknowledge={handleAcknowledge}
            onResolve={handleResolve}
          />
        </Grid>

        {selectedAlert && (
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, position: 'sticky', top: 80 }}>
              <Typography variant="h6" gutterBottom>
                Alert Details
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Alert ID
                </Typography>
                <Typography variant="body1" fontWeight="medium">
                  {selectedAlert.id}
                </Typography>
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Source
                </Typography>
                <Typography variant="body1" fontWeight="medium">
                  {selectedAlert.source}
                </Typography>
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Last Updated
                </Typography>
                <Typography variant="body1" fontWeight="medium">
                  {new Date(selectedAlert.lastUpdatedAt).toLocaleString()}
                </Typography>
              </Box>

              <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                Related Logs
              </Typography>
              {relatedLogs.length > 0 ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {relatedLogs.map((log) => (
                    <Paper key={log.id} variant="outlined" sx={{ p: 1.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 0.5 }}>
                        [{log.level}] {log.message}
                      </Typography>
                    </Paper>
                  ))}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No related logs found
                </Typography>
              )}
            </Paper>
          </Grid>
        )}
      </Grid>
    </Container>
  );
};

export default Alerts;