import { useState, useMemo } from 'react';
import {
  Container,
  Typography,
  Box,
  ToggleButtonGroup,
  ToggleButton,
  Paper,
  Grid,
} from '@mui/material';
import AlertList from '@/components/AlertList';
import EnvironmentFilter from '@/components/EnvironmentFilter';
import { alerts } from '@/data/mockAlerts';
import { logEvents } from '@/data/mockLogs';

export const Alerts = () => {
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [selectedEnv, setSelectedEnv] = useState('All');
  const [selectedAlert, setSelectedAlert] = useState(null);

  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert) => {
      const matchesSeverity = selectedSeverity === 'all' || alert.severity === selectedSeverity;
      const matchesStatus = selectedStatus === 'all' || alert.status === selectedStatus;
      const matchesEnv = selectedEnv === 'All' || alert.environment === selectedEnv;
      return matchesSeverity && matchesStatus && matchesEnv;
    });
  }, [selectedSeverity, selectedStatus, selectedEnv]);

  const handleAcknowledge = (alertId) => {
    console.log('Acknowledging alert:', alertId);
    // TODO: Replace with real API call
  };

  const handleResolve = (alertId) => {
    console.log('Resolving alert:', alertId);
    // TODO: Replace with real API call
  };

  const relatedLogs = useMemo(() => {
    if (!selectedAlert) return [];
    return logEvents
      .filter((log) => log.serviceName === selectedAlert.serviceName)
      .slice(0, 5);
  }, [selectedAlert]);

  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Alerts
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Manage and respond to system alerts and anomalies
      </Typography>

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
