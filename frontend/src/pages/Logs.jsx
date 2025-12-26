import { useState, useMemo } from 'react';
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
} from '@mui/material';
import EnvironmentFilter from '@/components/EnvironmentFilter';
import LogTimeline from '@/components/LogTimeline';
import StatusChip from '@/components/StatusChip';
import { logStreams, logEvents } from '@/data/mockLogs';

export const Logs = () => {
  const [selectedEnv, setSelectedEnv] = useState('All');
  const [selectedService, setSelectedService] = useState('All');
  const [searchText, setSearchText] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('all');

  const filteredEvents = useMemo(() => {
    return logEvents.filter((event) => {
      const matchesEnv = selectedEnv === 'All' || event.environment === selectedEnv;
      const matchesService = selectedService === 'All' || event.serviceName === selectedService;
      const matchesSearch = event.message.toLowerCase().includes(searchText.toLowerCase());
      const matchesLevel = selectedLevel === 'all' || event.level === selectedLevel;
      return matchesEnv && matchesService && matchesSearch && matchesLevel;
    });
  }, [selectedEnv, selectedService, searchText, selectedLevel]);

  const services = ['All', ...new Set(logEvents.map((e) => e.serviceName))];

  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Logs
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Monitor log streams and trace anomalies across services
      </Typography>

      {/* Log Ingestion Status */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Log Ingestion Status
        </Typography>
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
              No logs match your filters
            </Typography>
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default Logs;
