import { Alert, AlertTitle, Box, Button, Stack, Paper } from '@mui/material';
import StatusChip from './StatusChip';

const severityMap = {
  critical: 'error',
  high: 'warning',
  medium: 'info',
  low: 'info',
};

export const AlertList = ({ alerts, onSelect, onAcknowledge, onResolve }) => {
  return (
    <Stack spacing={2}>
      {alerts.map((alert) => (
        <Paper
          key={alert.id}
          elevation={2}
          sx={{
            p: 2,
            cursor: 'pointer',
            '&:hover': {
              boxShadow: 4,
            },
          }}
          onClick={() => onSelect(alert)}
        >
          <Alert
            severity={severityMap[alert.severity] || 'info'}
            sx={{ mb: 1 }}
            action={
              <Box sx={{ display: 'flex', gap: 1 }}>
                {alert.status === 'open' && (
                  <Button
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      onAcknowledge(alert.id);
                    }}
                  >
                    Acknowledge
                  </Button>
                )}
                {alert.status !== 'resolved' && (
                  <Button
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      onResolve(alert.id);
                    }}
                  >
                    Resolve
                  </Button>
                )}
              </Box>
            }
          >
            <AlertTitle>{alert.title}</AlertTitle>
            {alert.description}
          </Alert>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
            <StatusChip value={alert.severity} type="severity" />
            <StatusChip value={alert.status} type="status" />
            <StatusChip value={alert.environment} type="status" />
            <StatusChip value={alert.source} type="status" />
          </Box>
          <Box sx={{ mt: 1, fontSize: '0.875rem', color: 'text.secondary' }}>
            Service: {alert.serviceName} | Created: {new Date(alert.createdAt).toLocaleString()}
          </Box>
        </Paper>
      ))}
    </Stack>
  );
};

export default AlertList;
