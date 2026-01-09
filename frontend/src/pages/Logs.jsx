import { useState, useMemo, useEffect, useRef, useCallback } from 'react';
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
import StatusChip from '@/components/StatusChip';
import api from '@/api/http';

// Cache storage outside component to persist across unmounts
let cachedData = {
  logStreams: null,
  logEvents: null,
  timestamp: null,
};

// Pre-fetch data as soon as module loads (even before component mounts)
let initialFetchPromise = null;
let prefetchFailed = false;

const prefetchData = () => {
  if (!initialFetchPromise && !cachedData.logStreams) {
    initialFetchPromise = Promise.all([
      api.get('/logs/streams').catch(() => ({ data: [] })),
      api.get('/logs/events').catch(() => ({ data: [] })),
    ]).then(([streamsResponse, eventsResponse]) => {
      const streams = streamsResponse.data || [];
      const events = eventsResponse.data || [];
      
      // Check if we got actual data
      if (streams.length === 0 && events.length === 0) {
        prefetchFailed = true;
      }
      
      const data = {
        logStreams: streams,
        logEvents: events,
        timestamp: Date.now(),
      };
      cachedData = data;
      return data;
    }).catch(() => {
      prefetchFailed = true;
      return {
        logStreams: [],
        logEvents: [],
        timestamp: Date.now(),
      };
    });
  }
  return initialFetchPromise;
};

// Start prefetching immediately when module loads
prefetchData();

export const Logs = () => {
  const [selectedEnv, setSelectedEnv] = useState('All');
  const [selectedService, setSelectedService] = useState('All');
  const [searchText, setSearchText] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('all');
  const [logStreams, setLogStreams] = useState(cachedData.logStreams || []);
  const [logEvents, setLogEvents] = useState(cachedData.logEvents || []);
  const pollIntervalRef = useRef(null);
  const isMountedRef = useRef(true);
  const lastFetchTime = useRef(cachedData.timestamp || 0);

  const fetchLogsData = useCallback(async (isPolling = false) => {
    try {
      // Throttle: Don't fetch if last fetch was less than 5 seconds ago (unless manual refresh)
      if (isPolling && Date.now() - lastFetchTime.current < 5000) {
        return;
      }

      const [streamsResponse, eventsResponse] = await Promise.all([
        api.get('/logs/streams').catch(() => ({ data: [] })),
        api.get('/logs/events').catch(() => ({ data: [] })),
      ]);

      if (!isMountedRef.current) return;

      lastFetchTime.current = Date.now();
      const newStreams = streamsResponse.data || [];
      const newEvents = eventsResponse.data || [];

      // Fast shallow comparison - only update if lengths differ
      const shouldUpdate = 
        newEvents.length !== logEvents.length || 
        newStreams.length !== logStreams.length;

      if (shouldUpdate || !isPolling) {
        // Batch state updates
        setLogStreams(newStreams);
        setLogEvents(newEvents);
        
        cachedData = {
          logStreams: newStreams,
          logEvents: newEvents,
          timestamp: Date.now(),
        };
        
        if (isPolling && shouldUpdate) {
          console.log(`Logs updated: ${newEvents.length} events, ${newStreams.length} streams`);
        }
      }
    } catch (err) {
      console.error('Error fetching logs data:', err);
    }
  }, [logEvents.length, logStreams.length]);

  const startPolling = useCallback(() => {
    if (!pollIntervalRef.current) {
      pollIntervalRef.current = setInterval(() => {
        fetchLogsData(true);
      }, 30000);
    }
  }, [fetchLogsData]);

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    isMountedRef.current = true;

    const loadData = async () => {
      // If prefetch failed or returned empty data, retry
      if (prefetchFailed || (cachedData.logStreams && cachedData.logStreams.length === 0)) {
        // Reset flags
        initialFetchPromise = null;
        prefetchFailed = false;
        await fetchLogsData(false);
      } else if (initialFetchPromise) {
        // Use prefetched data if available
        try {
          const data = await initialFetchPromise;
          if (isMountedRef.current && data) {
            setLogStreams(data.logStreams);
            setLogEvents(data.logEvents);
          }
        } catch (err) {
          // If prefetch failed, try again
          await fetchLogsData(false);
        }
      } else {
        // No prefetch, fetch normally
        await fetchLogsData(false);
      }
    };

    loadData();
    startPolling();

    return () => {
      isMountedRef.current = false;
      stopPolling();
    };
  }, [fetchLogsData, startPolling, stopPolling]);

  const handleRefresh = useCallback(() => {
    lastFetchTime.current = 0; // Reset throttle
    fetchLogsData(false);
  }, [fetchLogsData]);

  // Memoize filtered events with optimized filtering
  const filteredEvents = useMemo(() => {
    if (logEvents.length === 0) return [];
    
    const lowerSearch = searchText.toLowerCase();
    const isAllEnv = selectedEnv === 'All';
    const isAllService = selectedService === 'All';
    const isAllLevel = selectedLevel === 'all';

    // Fast path: no filters
    if (isAllEnv && isAllService && !lowerSearch && isAllLevel) {
      return logEvents;
    }

    return logEvents.filter((event) => {
      if (!isAllEnv && event.environment !== selectedEnv) return false;
      if (!isAllService && event.serviceName !== selectedService) return false;
      if (!isAllLevel && event.level !== selectedLevel) return false;
      if (lowerSearch && !event.message.toLowerCase().includes(lowerSearch)) return false;
      return true;
    });
  }, [selectedEnv, selectedService, searchText, selectedLevel, logEvents]);

  // Memoize services list
  const services = useMemo(() => 
    ['All', ...new Set(logEvents.map((e) => e.serviceName))],
    [logEvents]
  );

  return (
    <Container maxWidth="xl">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h4" gutterBottom fontWeight="bold">
            Logs
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor log streams and trace anomalies across services
          </Typography>
        </Box>
        <Tooltip title="Refresh logs">
          <IconButton onClick={handleRefresh} color="primary">
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Log Ingestion Status */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Log Ingestion Status
        </Typography>
        {logStreams.length > 0 ? (
          <Grid container spacing={2}>
            {logStreams.map((stream) => (
              <Grid item xs={12} sm={6} md={4} lg={2.4} key={stream.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" fontWeight="bold">
                        {stream.serviceName}
                      </Typography>
                      <StatusChip value={stream.status} type="status" />
                    </Box>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Source: {stream.source}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Environment: {stream.environment}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Lag: {stream.ingestionLagSec.toFixed(1)}s
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        ) : (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="body1" color="text.secondary">
              No log streams available
            </Typography>
          </Box>
        )}
      </Box>

      {/* Log Controls */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <EnvironmentFilter
          value={selectedEnv}
          onChange={(e) => setSelectedEnv(e.target.value)}
        />
        <TextField
          select
          label="Service"
          value={selectedService}
          onChange={(e) => setSelectedService(e.target.value)}
          size="small"
          sx={{ minWidth: 200 }}
          SelectProps={{ native: true }}
        >
          {services.map((service) => (
            <option key={service} value={service}>
              {service}
            </option>
          ))}
        </TextField>
        <TextField
          label="Search messages"
          variant="outlined"
          size="small"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          sx={{ minWidth: 250 }}
        />
        <ToggleButtonGroup
          value={selectedLevel}
          exclusive
          onChange={(e, val) => val && setSelectedLevel(val)}
          size="small"
        >
          <ToggleButton value="all">All</ToggleButton>
          <ToggleButton value="INFO">Info</ToggleButton>
          <ToggleButton value="WARN">Warn</ToggleButton>
          <ToggleButton value="ERROR">Error</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Log Timeline */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Log Timeline
        </Typography>
        {filteredEvents.length > 0 ? (
          <LogTimeline events={filteredEvents} />
        ) : (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="body1" color="text.secondary">
              {logEvents.length === 0 ? 'No logs available' : 'No logs match your filters'}
            </Typography>
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default Logs;