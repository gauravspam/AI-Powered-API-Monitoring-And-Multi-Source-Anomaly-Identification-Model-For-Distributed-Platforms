import { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Drawer,
  IconButton,
  Chip,
  Button,
  Tooltip,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { Close as CloseIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import StatusChip from '@/components/StatusChip';
import EnvironmentFilter from '@/components/EnvironmentFilter';
import api from '@/api/http';

// ==================== CACHING LAYER ====================
// Cache storage outside component to persist across unmounts
let cachedData = {
  services: null,
  anomalies: null,
  timestamp: null,
};

// Pre-fetch data as soon as module loads (even before component mounts)
let initialFetchPromise = null;
let prefetchFailed = false;

const prefetchData = () => {
  if (!initialFetchPromise && !cachedData.services) {
    initialFetchPromise = Promise.all([
      api.get('/services').catch(() => ({ data: [] })),
      api.get('/dashboard/anomalies').catch(() => ({ data: [] })),
    ]).then(([servicesResponse, anomaliesResponse]) => {
      const services = servicesResponse.data || [];
      const anomalies = anomaliesResponse.data || [];

      // Check if we got actual data
      if (services.length === 0 && anomalies.length === 0) {
        prefetchFailed = true;
      }

      const data = {
        services: services,
        anomalies: anomalies,
        timestamp: Date.now(),
      };
      cachedData = data;
      return data;
    }).catch(() => {
      prefetchFailed = true;
      return {
        services: [],
        anomalies: [],
        timestamp: Date.now(),
      };
    });
  }
  return initialFetchPromise;
};

// Start prefetching immediately when module loads
prefetchData();

const columns = [
  { field: 'name', headerName: 'Service', width: 180 },
  { field: 'ownerTeam', headerName: 'Owner Team', width: 150 },
  { field: 'environment', headerName: 'Environment', width: 130 },
  {
    field: 'status',
    headerName: 'Status',
    width: 120,
    renderCell: (params) => <StatusChip value={params.value} type="status" />,
  },
  {
    field: 'avgLatencyMs',
    headerName: 'Avg Latency (ms)',
    width: 150,
    type: 'number',
  },
  {
    field: 'errorRate',
    headerName: 'Error Rate (%)',
    width: 130,
    type: 'number',
    valueFormatter: (value) => value?.toFixed(2),
  },
  {
    field: 'anomalyRate',
    headerName: 'Anomaly Rate (%)',
    width: 150,
    type: 'number',
    valueFormatter: (value) => value?.toFixed(2),
  },
  {
    field: 'lastDeploymentAt',
    headerName: 'Last Deployment',
    width: 180,
    valueFormatter: (value) => new Date(value).toLocaleString(),
  },
  {
    field: 'requestPerMin',
    headerName: 'RPM',
    width: 120,
    type: 'number',
    valueFormatter: (value) => value?.toLocaleString(),
  },
];

// ==================== COMPONENT ====================

export const Services = () => {
  // State management - only for UI state
  const [searchText, setSearchText] = useState('');
  const [selectedEnv, setSelectedEnv] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [selectedService, setSelectedService] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [services, setServices] = useState(cachedData.services || []);
  const [anomalies, setAnomalies] = useState(cachedData.anomalies || []);

  // Refs for managing lifecycle and throttling
  const pollIntervalRef = useRef(null);
  const isMountedRef = useRef(true);
  const lastFetchTime = useRef(cachedData.timestamp || 0);

  // Fetch services and anomalies data
  const fetchServicesData = useCallback(async (isPolling = false) => {
    try {
      // Throttle: Don't fetch if last fetch was less than 5 seconds ago (unless manual refresh)
      if (isPolling && Date.now() - lastFetchTime.current < 5000) {
        return;
      }

      const [servicesResponse, anomaliesResponse] = await Promise.all([
        api.get('/services').catch(() => ({ data: [] })),
        api.get('/dashboard/anomalies').catch(() => ({ data: [] })),
      ]);

      // Don't update if component unmounted
      if (!isMountedRef.current) return;

      lastFetchTime.current = Date.now();
      const newServices = servicesResponse.data || [];
      const newAnomalies = anomaliesResponse.data || [];

      // Fast shallow comparison - only update if lengths differ
      const shouldUpdate =
        newAnomalies.length !== anomalies.length ||
        newServices.length !== services.length;

      if (shouldUpdate || !isPolling) {
        setServices(newServices);
        setAnomalies(newAnomalies);

        // Update module-level cache
        cachedData = {
          services: newServices,
          anomalies: newAnomalies,
          timestamp: Date.now(),
        };

        if (isPolling && shouldUpdate) {
          console.log(`Services updated: ${newServices.length} services, ${newAnomalies.length} anomalies`);
        }
      }
    } catch (err) {
      console.error('Error fetching services data:', err);
    }
  }, [anomalies.length, services.length]);

  // Start background polling
  const startPolling = useCallback(() => {
    if (!pollIntervalRef.current) {
      pollIntervalRef.current = setInterval(() => {
        fetchServicesData(true);
      }, 30000); // 30 seconds
    }
  }, [fetchServicesData]);

  // Stop background polling
  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  }, []);

  // Setup subscriptions and initial data on mount
  useEffect(() => {
    isMountedRef.current = true;

    const loadData = async () => {
      // EDGE CASE 1: If prefetch failed or returned empty data (server was down), retry
      if (prefetchFailed || (cachedData.services && cachedData.services.length === 0)) {
        // Reset flags to allow retry
        initialFetchPromise = null;
        prefetchFailed = false;
        console.log('Retrying initial fetch (server may have been down)...');
        await fetchServicesData(false);
      } else if (initialFetchPromise) {
        // Use prefetched data if available
        try {
          const data = await initialFetchPromise;
          if (isMountedRef.current && data) {
            setServices(data.services);
            setAnomalies(data.anomalies);
          }
        } catch (err) {
          // If prefetch failed, try again
          await fetchServicesData(false);
        }
      } else {
        // No prefetch available, fetch normally
        await fetchServicesData(false);
      }
    };

    loadData();
    startPolling();

    return () => {
      isMountedRef.current = false;
      stopPolling();
    };
  }, [fetchServicesData, startPolling, stopPolling]);

  // Manual refresh handler
  const handleRefresh = useCallback(() => {
    lastFetchTime.current = 0; // Reset throttle to allow immediate fetch
    fetchServicesData(false);
  }, [fetchServicesData]);

  // Memoized filtered services
  const filteredServices = useMemo(() => {
    if (services.length === 0) return [];

    const lowerSearch = searchText.toLowerCase();
    const isAllEnv = selectedEnv === 'All';
    const isAllStatus = selectedStatus === 'All';

    // Fast path: no filters
    if (isAllEnv && isAllStatus && !lowerSearch) {
      return services;
    }

    return services.filter((service) => {
      if (!isAllEnv && service.environment !== selectedEnv) return false;
      if (!isAllStatus && service.status !== selectedStatus) return false;
      if (lowerSearch && !service.name.toLowerCase().includes(lowerSearch)) return false;
      return true;
    });
  }, [searchText, selectedEnv, selectedStatus, services]);

  // Memoized service anomalies
  const serviceAnomalies = useMemo(() => {
    if (!selectedService || anomalies.length === 0) return [];
    return anomalies.filter((a) => a.serviceName === selectedService.name);
  }, [selectedService, anomalies]);

  // Callback for row click
  const handleRowClick = useCallback((params) => {
    setSelectedService(params.row);
    setDrawerOpen(true);
  }, []);

  return (
    <Container maxWidth="xl">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h4" gutterBottom fontWeight="bold">
            Services
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor and manage API services across distributed environments
          </Typography>
        </Box>
        <Tooltip title="Refresh services">
          <IconButton onClick={handleRefresh} color="primary">
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <TextField
            label="Search services"
            variant="outlined"
            size="small"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            sx={{ minWidth: 250 }}
          />
          <EnvironmentFilter
            value={selectedEnv}
            onChange={(e) => setSelectedEnv(e.target.value)}
          />
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={selectedStatus}
              label="Status"
              onChange={(e) => setSelectedStatus(e.target.value)}
            >
              <MenuItem value="All">All Statuses</MenuItem>
              <MenuItem value="healthy">Healthy</MenuItem>
              <MenuItem value="degraded">Degraded</MenuItem>
              <MenuItem value="down">Down</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Box sx={{ height: 600, width: '100%' }}>
          <DataGrid
            rows={filteredServices}
            columns={columns}
            pageSize={10}
            rowsPerPageOptions={[10, 25, 50]}
            onRowClick={handleRowClick}
            disableSelectionOnClick
            sx={{
              '& .MuiDataGrid-row:hover': {
                cursor: 'pointer',
              },
            }}
          />
        </Box>
      </Paper>

      {/* Service Detail Drawer */}
      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        PaperProps={{ sx: { width: 450, p: 3 } }}
      >
        {selectedService && (
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h5" fontWeight="bold">
                {selectedService.name}
              </Typography>
              <IconButton onClick={() => setDrawerOpen(false)}>
                <CloseIcon />
              </IconButton>
            </Box>

            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Owner Team
              </Typography>
              <Typography variant="body1" fontWeight="medium">
                {selectedService.ownerTeam}
              </Typography>
            </Box>

            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Environment
              </Typography>
              <StatusChip value={selectedService.environment} type="status" />
            </Box>

            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Status
              </Typography>
              <StatusChip value={selectedService.status} type="status" />
            </Box>

            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Tags
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {selectedService.tags.map((tag) => (
                  <Chip key={tag} label={tag} size="small" variant="outlined" />
                ))}
              </Box>
            </Box>

            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Metrics
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Avg Latency</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {selectedService.avgLatencyMs} ms
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Error Rate</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {selectedService.errorRate}%
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Anomaly Rate</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {selectedService.anomalyRate}%
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Requests/Min</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {selectedService.requestPerMin.toLocaleString()}
                  </Typography>
                </Box>
              </Box>
            </Box>

            <Box>
              <Typography variant="h6" gutterBottom>
                Recent Anomalies
              </Typography>
              {serviceAnomalies.length > 0 ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {serviceAnomalies.map((anomaly) => (
                    <Paper key={anomaly.id} sx={{ p: 2 }} variant="outlined">
                      <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                        <StatusChip value={anomaly.severity} type="severity" />
                        <StatusChip value={anomaly.status} type="status" />
                      </Box>
                      <Typography variant="body2">{anomaly.endpoint}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        Score: {anomaly.score.toFixed(2)}
                      </Typography>
                    </Paper>
                  ))}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No recent anomalies
                </Typography>
              )}
            </Box>
          </Box>
        )}
      </Drawer>
    </Container>
  );
};

export default Services;
