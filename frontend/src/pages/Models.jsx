import { useState, useMemo } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  Alert,
  AlertTitle,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import StatusChip from '@/components/StatusChip';
import { models } from '@/data/mockModels';

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
    valueFormatter: (value) => new Date(value).toLocaleString(),
  },
  {
    field: 'accuracy',
    headerName: 'Accuracy (%)',
    width: 130,
    type: 'number',
    valueFormatter: (value) => value?.toFixed(1),
  },
];

export const Models = () => {
  const [selectedType, setSelectedType] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');

  const filteredModels = useMemo(() => {
    return models.filter((model) => {
      const matchesType = selectedType === 'All' || model.type === selectedType;
      const matchesStatus = selectedStatus === 'All' || model.status === selectedStatus;
      return matchesType && matchesStatus;
    });
  }, [selectedType, selectedStatus]);

  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom fontWeight="bold">
        AI Models
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Monitor AI model deployments and performance metrics
      </Typography>

      {/* Model Type Legend */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <AlertTitle>Model Types</AlertTitle>
        <Typography variant="body2" component="div">
          <strong>MSIF-LSTM:</strong> Multi-Source Information Fusion using LSTM networks for
          detecting anomalies by fusing log, trace, and metric data.
          <br />
          <strong>PLE-GRU:</strong> Probability Label Estimation using GRU networks to estimate
          anomaly probabilities with limited labeled data.
          <br />
          <strong>MDN-EVL Forecaster:</strong> Mixture Density Network for Event Value Learning,
          forecasting tail events and rare anomalies.
        </Typography>
      </Alert>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2 }}>
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
        </Box>
      </Paper>

      {/* Models Table */}
      <Paper sx={{ p: 2 }}>
        <Box sx={{ height: 500, width: '100%' }}>
          <DataGrid
            rows={filteredModels}
            columns={columns}
            pageSize={10}
            rowsPerPageOptions={[10, 25]}
            disableSelectionOnClick
          />
        </Box>
      </Paper>
    </Container>
  );
};

export default Models;
