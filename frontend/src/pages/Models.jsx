import { useState, useMemo, useEffect, useRef, useCallback } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TextField,
  IconButton,
  Tooltip,
} from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';
import { DataGrid } from '@mui/x-data-grid';
import StatusChip from '@/components/StatusChip';
import api from '@/api/http';

// DataGrid Column Definitions
const columns = [
  { field: 'name', headerName: 'Model Name', width: 200 },
  { field: 'version', headerName: 'Version', width: 120 },
  { field: 'type', headerName: 'Type', width: 150 },
  {
    field: 'status',
    headerName: 'Status',
    width: 120,
    renderCell: (params) => <StatusChip value={params.value} type="status" />,
  },
  {
    field: 'latencyMs',
    headerName: 'Latency (ms)',
    width: 130,
    type: 'number',
  },
  {
    field: 'throughputPerSec',
    headerName: 'Throughput/sec',
    width: 150,
    type: 'number',
    valueFormatter: (value) => value?.toLocaleString(),
  },
  {
    field: 'lastRetrainAt',
    headerName: 'Last Retrain',
    width: 180,
    valueFormatter: (value) => value ? new Date(value).toLocaleString() : 'N/A',
  },
  {
    field: 'accuracy',
    headerName: 'Accuracy (%)',
    width: 130,
    type: 'number',
    valueFormatter: (value) => value?.toFixed(1),
  },
];

// --- LOGIC: CACHING & PREFETCHING ---

let cachedData = {
  models: null,
  timestamp: null,
};

let initialFetchPromise = null;
let prefetchFailed = false;

const prefetchData = () => {
  if (!initialFetchPromise && !cachedData.models) {
    initialFetchPromise = api.get('/models')
      .then((response) => {
        const models = response.data || [];
        if (models.length === 0) prefetchFailed = true;
        
        cachedData = { models, timestamp: Date.now() };
        return cachedData;
      })
      .catch(() => {
        prefetchFailed = true;
        return { models: [], timestamp: Date.now() };
      });
  }
  return initialFetchPromise;
};

// Start fetching as soon as the module is imported
prefetchData();

export const Models = () => {
  // --- STATE ---
  const [models, setModels] = useState(cachedData.models || []);
  const [selectedType, setSelectedType] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [searchText, setSearchText] = useState('');
  
  const pollIntervalRef = useRef(null);
  const isMountedRef = useRef(true);
  const lastFetchTime = useRef(cachedData.timestamp || 0);

  // --- API CALLING LOGIC ---

  const fetchModelsData = useCallback(async (isPolling = false) => {
    try {
      // Throttle background polling (5s)
      if (isPolling && Date.now() - lastFetchTime.current < 5000) {
        return;
      }

      const response = await api.get('/models');
      
      if (!isMountedRef.current) return;

      const newModels = response.data || [];
      lastFetchTime.current = Date.now();

      // Update state only if data changed or if it's a manual refresh
      if (newModels.length !== models.length || !isPolling) {
        setModels(newModels);
        cachedData = {
          models: newModels,
          timestamp: Date.now(),
        };
      }
    } catch (err) {
      console.error('Error fetching models data:', err);
    }
  }, [models.length]);

  const startPolling = useCallback(() => {
    if (!pollIntervalRef.current) {
      pollIntervalRef.current = setInterval(() => {
        fetchModelsData(true);
      }, 30000); // Poll every 30s
    }
  }, [fetchModelsData]);

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  }, []);

  // --- LIFECYCLE ---

  useEffect(() => {
    isMountedRef.current = true;

    const loadData = async () => {
      if (prefetchFailed || (cachedData.models && cachedData.models.length === 0)) {
        initialFetchPromise = null;
        prefetchFailed = false;
        await fetchModelsData(false);
      } else if (initialFetchPromise) {
        try {
          const data = await initialFetchPromise;
          if (isMountedRef.current && data) {
            setModels(data.models);
          }
        } catch (err) {
          await fetchModelsData(false);
        }
      } else {
        await fetchModelsData(false);
      }
    };

    loadData();
    startPolling();

    return () => {
      isMountedRef.current = false;
      stopPolling();
    };
  }, [fetchModelsData, startPolling, stopPolling]);

  const handleRefresh = useCallback(() => {
    lastFetchTime.current = 0; // Bypass throttle
    fetchModelsData(false);
  }, [fetchModelsData]);

  // --- MEMOIZED FILTERING ---

  const filteredModels = useMemo(() => {
    if (models.length === 0) return [];

    const lowerSearch = searchText.toLowerCase();
    const isAllType = selectedType === 'All';
    const isAllStatus = selectedStatus === 'All';

    // Fast path: No filters applied
    if (isAllType && isAllStatus && !lowerSearch) {
      return models;
    }

    return models.filter((model) => {
      if (!isAllType && model.type !== selectedType) return false;
      if (!isAllStatus && model.status !== selectedStatus) return false;
      if (lowerSearch && !model.name.toLowerCase().includes(lowerSearch)) return false;
      return true;
    });
  }, [models, selectedType, selectedStatus, searchText]);

  return (
    <Container maxWidth="xl">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h4" gutterBottom fontWeight="bold">
            AI Models
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor AI model deployments and performance metrics
          </Typography>
        </Box>
        <Tooltip title="Refresh models">
          <IconButton onClick={handleRefresh} color="primary">
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Model Type</InputLabel>
            <Select
              value={selectedType}
              label="Model Type"
              onChange={(e) => setSelectedType(e.target.value)}
            >
              <MenuItem value="All">All Types</MenuItem>
              <MenuItem value="detection">Detection</MenuItem>
              <MenuItem value="label_estimation">Label Estimation</MenuItem>
              <MenuItem value="forecasting">Forecasting</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={selectedStatus}
              label="Status"
              onChange={(e) => setSelectedStatus(e.target.value)}
            >
              <MenuItem value="All">All Statuses</MenuItem>
              <MenuItem value="online">Online</MenuItem>
              <MenuItem value="warming">Warming</MenuItem>
              <MenuItem value="offline">Offline</MenuItem>
            </Select>
          </FormControl>

          <TextField
            label="Search models"
            variant="outlined"
            size="small"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            sx={{ minWidth: 250 }}
          />
        </Box>
      </Paper>

      <Paper sx={{ p: 2 }}>
        <Box sx={{ height: 600, width: '100%' }}>
          <DataGrid
            rows={filteredModels}
            columns={columns}
            getRowId={(row) => row.id || row.name}
            pageSize={10}
            rowsPerPageOptions={[10, 25, 50]}
            disableSelectionOnClick
            density="comfortable"
          />
        </Box>
      </Paper>
    </Container>
  );
};

export default Models;