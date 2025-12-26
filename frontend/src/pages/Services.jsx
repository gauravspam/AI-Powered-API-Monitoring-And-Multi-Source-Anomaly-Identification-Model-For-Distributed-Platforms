import { useState, useMemo } from 'react';
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
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { Close as CloseIcon } from '@mui/icons-material';
import StatusChip from '@/components/StatusChip';
import EnvironmentFilter from '@/components/EnvironmentFilter';
import { services } from '@/data/mockServices';
import { recentAnomalies } from '@/data/mockDashboard';

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

export const Services = () => {
  const [searchText, setSearchText] = useState('');
  const [selectedEnv, setSelectedEnv] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [selectedService, setSelectedService] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const filteredServices = useMemo(() => {
    return services.filter((service) => {
      const matchesSearch = service.name.toLowerCase().includes(searchText.toLowerCase());
      const matchesEnv = selectedEnv === 'All' || service.environment === selectedEnv;
      const matchesStatus = selectedStatus === 'All' || service.status === selectedStatus;
      return matchesSearch && matchesEnv && matchesStatus;
    });
  }, [searchText, selectedEnv, selectedStatus]);

  const handleRowClick = (params) => {
    setSelectedService(params.row);
    setDrawerOpen(true);
  };

  const serviceAnomalies = useMemo(() => {
    if (!selectedService) return [];
    return recentAnomalies.filter((a) => a.serviceName === selectedService.name);
  }, [selectedService]);

  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Services
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Monitor and manage API services across distributed environments
      </Typography>

      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
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
