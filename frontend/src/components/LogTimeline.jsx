import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineDot,
  TimelineConnector,
  TimelineContent,
  TimelineOppositeContent,
} from '@mui/lab';
import { Paper, Typography, Chip, Box } from '@mui/material';
import {
  Info as InfoIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';

const levelConfig = {
  INFO: { color: 'info', icon: InfoIcon },
  WARN: { color: 'warning', icon: WarningIcon },
  ERROR: { color: 'error', icon: ErrorIcon },
};

export const LogTimeline = ({ events }) => {
  return (
    <Timeline>
      {events.map((event, index) => {
        const config = levelConfig[event.level] || levelConfig.INFO;
        const IconComponent = config.icon;

        return (
          <TimelineItem key={event.id}>
            <TimelineOppositeContent color="text.secondary" sx={{ flex: 0.2 }}>
              <Typography variant="body2">
                {new Date(event.timestamp).toLocaleTimeString()}
              </Typography>
            </TimelineOppositeContent>
            <TimelineSeparator>
              <TimelineDot color={config.color}>
                <IconComponent fontSize="small" />
              </TimelineDot>
              {index < events.length - 1 && <TimelineConnector />}
            </TimelineSeparator>
            <TimelineContent>
              <Paper elevation={3} sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', gap: 1, mb: 1, flexWrap: 'wrap' }}>
                  <Chip label={event.level} size="small" color={config.color} />
                  <Chip label={event.serviceName} size="small" variant="outlined" />
                  <Chip label={event.environment} size="small" variant="outlined" />
                  {event.isAnomalyFlagged && (
                    <Chip label="ANOMALY" size="small" color="error" />
                  )}
                </Box>
                <Typography variant="body2">{event.message}</Typography>
                {event.correlationId && (
                  <Typography variant="caption" color="text.secondary">
                    Correlation ID: {event.correlationId}
                  </Typography>
                )}
              </Paper>
            </TimelineContent>
          </TimelineItem>
        );
      })}
    </Timeline>
  );
};

export default LogTimeline;
