import { Chip } from '@mui/material';

const severityColors = {
  critical: 'error',
  high: 'warning',
  medium: 'info',
  low: 'default',
};

const statusColors = {
  open: 'error',
  investigating: 'warning',
  acknowledged: 'info',
  mitigated: 'success',
  resolved: 'success',
  healthy: 'success',
  degraded: 'warning',
  down: 'error',
  online: 'success',
  warming: 'warning',
  offline: 'error',
  delayed: 'warning',
};

export const StatusChip = ({ value, type = 'severity' }) => {
  const colorMap = type === 'severity' ? severityColors : statusColors;
  const color = colorMap[value?.toLowerCase()] || 'default';

  return (
    <Chip
      label={value}
      color={color}
      size="small"
      sx={{ fontWeight: 600, textTransform: 'capitalize' }}
    />
  );
};

export default StatusChip;
