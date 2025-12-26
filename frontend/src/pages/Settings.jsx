import { useState } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  TextField,
  Switch,
  FormControlLabel,
  Button,
  Divider,
  Slider,
  Grid,
  Snackbar,
  Alert,
} from '@mui/material';

export const Settings = () => {
  const [kafkaBroker, setKafkaBroker] = useState('kafka.monitoring.local:9092');
  const [logTopic, setLogTopic] = useState('api-logs');
  const [metricTopic, setMetricTopic] = useState('api-metrics');
  const [slackEnabled, setSlackEnabled] = useState(true);
  const [slackWebhook, setSlackWebhook] = useState('https://hooks.slack.com/services/...');
  const [pagerDutyEnabled, setPagerDutyEnabled] = useState(false);
  const [pagerDutyKey, setPagerDutyKey] = useState('');
  const [thresholds, setThresholds] = useState({
    onPrem: 0.75,
    aws: 0.75,
    gcp: 0.75,
    azure: 0.75,
    multiCloud: 0.75,
  });
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  const handleSave = () => {
    // TODO: Replace with real API call
    console.log('Saving settings:', {
      kafka: { kafkaBroker, logTopic, metricTopic },
      alerting: { slackEnabled, slackWebhook, pagerDutyEnabled, pagerDutyKey },
      thresholds,
    });
    setSnackbarOpen(true);
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Settings
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Configure system settings and integrations
      </Typography>

      {/* API & Streaming */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          API & Streaming
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Configure Kafka and log ingestion endpoints
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            label="Kafka Broker URL"
            value={kafkaBroker}
            onChange={(e) => setKafkaBroker(e.target.value)}
            fullWidth
          />
          <TextField
            label="Log Topic Name"
            value={logTopic}
            onChange={(e) => setLogTopic(e.target.value)}
            fullWidth
          />
          <TextField
            label="Metric Topic Name"
            value={metricTopic}
            onChange={(e) => setMetricTopic(e.target.value)}
            fullWidth
          />
        </Box>
      </Paper>

      {/* Alerting */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Alerting
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Configure alert notifications and integrations
        </Typography>

        <Box sx={{ mb: 3 }}>
          <FormControlLabel
            control={
              <Switch
                checked={slackEnabled}
                onChange={(e) => setSlackEnabled(e.target.checked)}
              />
            }
            label="Enable Slack Integration"
          />
          {slackEnabled && (
            <TextField
              label="Slack Webhook URL"
              value={slackWebhook}
              onChange={(e) => setSlackWebhook(e.target.value)}
              fullWidth
              sx={{ mt: 2 }}
            />
          )}
        </Box>

        <Divider sx={{ my: 2 }} />

        <Box>
          <FormControlLabel
            control={
              <Switch
                checked={pagerDutyEnabled}
                onChange={(e) => setPagerDutyEnabled(e.target.checked)}
              />
            }
            label="Enable PagerDuty Integration"
          />
          {pagerDutyEnabled && (
            <TextField
              label="PagerDuty Routing Key"
              value={pagerDutyKey}
              onChange={(e) => setPagerDutyKey(e.target.value)}
              fullWidth
              sx={{ mt: 2 }}
            />
          )}
        </Box>
      </Paper>

      {/* Thresholds */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Anomaly Score Thresholds
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Set anomaly detection thresholds for each environment (0.0 - 1.0)
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" gutterBottom>
              On Premise: {thresholds.onPrem.toFixed(2)}
            </Typography>
            <Slider
              value={thresholds.onPrem}
              onChange={(e, val) => setThresholds({ ...thresholds, onPrem: val })}
              min={0}
              max={1}
              step={0.05}
              marks
              valueLabelDisplay="auto"
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" gutterBottom>
              AWS: {thresholds.aws.toFixed(2)}
            </Typography>
            <Slider
              value={thresholds.aws}
              onChange={(e, val) => setThresholds({ ...thresholds, aws: val })}
              min={0}
              max={1}
              step={0.05}
              marks
              valueLabelDisplay="auto"
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" gutterBottom>
              GCP: {thresholds.gcp.toFixed(2)}
            </Typography>
            <Slider
              value={thresholds.gcp}
              onChange={(e, val) => setThresholds({ ...thresholds, gcp: val })}
              min={0}
              max={1}
              step={0.05}
              marks
              valueLabelDisplay="auto"
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" gutterBottom>
              Azure: {thresholds.azure.toFixed(2)}
            </Typography>
            <Slider
              value={thresholds.azure}
              onChange={(e, val) => setThresholds({ ...thresholds, azure: val })}
              min={0}
              max={1}
              step={0.05}
              marks
              valueLabelDisplay="auto"
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" gutterBottom>
              Multi-Cloud: {thresholds.multiCloud.toFixed(2)}
            </Typography>
            <Slider
              value={thresholds.multiCloud}
              onChange={(e, val) => setThresholds({ ...thresholds, multiCloud: val })}
              min={0}
              max={1}
              step={0.05}
              marks
              valueLabelDisplay="auto"
            />
          </Grid>
        </Grid>
      </Paper>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <Button variant="contained" size="large" onClick={handleSave}>
          Save Changes
        </Button>
      </Box>

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity="success" onClose={() => setSnackbarOpen(false)}>
          Settings saved successfully!
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default Settings;
