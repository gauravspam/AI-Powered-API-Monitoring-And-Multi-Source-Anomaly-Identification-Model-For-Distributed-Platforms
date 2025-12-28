import { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Typography,
  Box,
  Paper,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Divider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import StatCard from '@/components/StatCard';
import AnomalyTable from '@/components/AnomalyTable';
import MetricChart from '@/components/MetricChart';
import EnvironmentFilter from '@/components/EnvironmentFilter';
import StatusChip from '@/components/StatusChip';
import { kpiCards, environmentSummary, recentAnomalies, trafficSeries } from '@/data/mockDashboard';

export const Dashboard = () => {
  // const [loading, setLoading] = useState(false);
  const [selectedEnv, setSelectedEnv] = useState('All');
  const [selectedSeverity, setSelectedSeverity] = useState('All');
  const [filteredAnomalies, setFilteredAnomalies] = useState([]);

  // useEffect(() => {
  //   // Simulate loading
  //   // setTimeout(() => setLoading(false), 800);
  //   setLoading(false)

  // }, []);

  useEffect(() => {
    let filtered = recentAnomalies;
    if (selectedEnv !== 'All') {
      filtered = filtered.filter((a) => a.environment === selectedEnv);
    }
    if (selectedSeverity !== 'All') {
      filtered = filtered.filter((a) => a.severity === selectedSeverity);
    }
    setFilteredAnomalies(filtered);
  }, [selectedEnv, selectedSeverity]);

  // if (loading) {
  //   return (
  //     <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
  //       <CircularProgress />
  //     </Box>
  //   );
  // }


  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Real-time monitoring and anomaly detection across distributed platforms
      </Typography>

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
                onChange={(e) => setSelectedSeverity(e.target.value)}
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
              onChange={(e) => setSelectedEnv(e.target.value)}
            />
          </Box>
        </Box>
        <AnomalyTable rows={filteredAnomalies} onRowClick={(params) => console.log(params.row)} />
      </Paper>
    </Container>
  );
};

export default Dashboard;
