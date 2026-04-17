import { useState, useEffect } from 'react';
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
import api from '@/api/http';

export const Settings = () => {
  const [settings, setSettings] = useState({
    alerting: {
      slackEnabled: false,
      slackWebhook: '',
      pagerDutyEnabled: false,
      pagerDutyKey: '',
    },
    thresholds: {
      onPrem: 0.75,
      aws: 0.75,
      gcp: 0.75,
      azure: 0.75,
      multiCloud: 0.75,
    },
  });
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  useEffect(() => {
    // Fetch current settings from the API
    api.get('/settings/configuration')
      .then((response) => {
        setSettings(response.data);
      })
      .catch((error) => {
        console.error('Error fetching settings:', error);
      });
  }, []);

  const handleSave = () => {
    // Update settings via the API
    api.post('/settings/update', settings)
      .then(() => {
        setSnackbarOpen(true);
      })
      .catch((error) => {
        console.error('Error saving settings:', error);
      });
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Settings
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Configure system settings and integrations
      </Typography>

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
                checked={settings.alerting.slackEnabled}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    alerting: {
                      ...settings.alerting,
                      slackEnabled: e.target.checked,
                    },
                  })
                }
              />
            }
            label="Enable Slack Integration"
          />
          {settings.alerting.slackEnabled && (
            <TextField
              label="Slack Webhook URL"
              value={settings.alerting.slackWebhook}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  alerting: {
                    ...settings.alerting,
                    slackWebhook: e.target.value,
                  },
                })
              }
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
                checked={settings.alerting.pagerDutyEnabled}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    alerting: {
                      ...settings.alerting,
                      pagerDutyEnabled: e.target.checked,
                    },
                  })
                }
              />
            }
            label="Enable PagerDuty Integration"
          />
          {settings.alerting.pagerDutyEnabled && (
            <TextField
              label="PagerDuty Routing Key"
              value={settings.alerting.pagerDutyKey}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  alerting: {
                    ...settings.alerting,
                    pagerDutyKey: e.target.value,
                  },
                })
              }
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
          {Object.keys(settings.thresholds).map((key) => (
            <Grid item xs={12} sm={6} key={key}>
              <Typography variant="body2" gutterBottom>
                {key.charAt(0).toUpperCase() + key.slice(1)}: {settings.thresholds[key].toFixed(2)}
              </Typography>
              <Slider
                value={settings.thresholds[key]}
                onChange={(e, val) =>
                  setSettings({
                    ...settings,
                    thresholds: {
                      ...settings.thresholds,
                      [key]: val,
                    },
                  })
                }
                min={0}
                max={1}
                step={0.05}
                marks
                valueLabelDisplay="auto"
              />
            </Grid>
          ))}
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
