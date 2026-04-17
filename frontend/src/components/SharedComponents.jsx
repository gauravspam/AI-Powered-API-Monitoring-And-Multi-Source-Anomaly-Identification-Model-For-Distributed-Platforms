import { Box, Chip, LinearProgress, Typography, Paper, TableRow, TableCell } from '@mui/material';
import { SEVERITY_COLORS } from '../theme';

export function SeverityBadge({ severity }) {
  const s = (severity || 'NORMAL').toUpperCase();
  const color = SEVERITY_COLORS[s] || SEVERITY_COLORS.NORMAL;
  return (
    <Chip
      label={s}
      size="small"
      sx={{
        backgroundColor: `${color}20`,
        color: color,
        border: `1px solid ${color}50`,
        fontWeight: 500,
        fontSize: '0.75rem',
        height: '24px',
      }}
    />
  );
}

export function StatusDot({ status }) {
  const s = (status || '').toLowerCase();
  const colorMap = {
    healthy: '#22c55e',
    online: '#22c55e',
    active: '#ef4444',
    degraded: '#eab308',
    down: '#ef4444',
    offline: '#6b7280',
    acknowledged: '#eab308',
    resolved: '#22c55e',
  };
  return (
    <Box
      component="span"
      sx={{
        width: 8,
        height: 8,
        borderRadius: '50%',
        backgroundColor: colorMap[s] || '#6b7280',
        display: 'inline-block',
        flexShrink: 0,
      }}
    />
  );
}

export function ScoreBar({ score, max = 1 }) {
  const pct = Math.min((score / max) * 100, 100);
  const color =
    score >= 0.8 ? '#ef4444' :
    score >= 0.6 ? '#f97316' :
    score >= 0.4 ? '#eab308' :
    score >= 0.2 ? '#22c55e' : '#6b7280';
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, width: '100%' }}>
      <LinearProgress
        variant="determinate"
        value={pct}
        sx={{
          flex: 1,
          height: 6,
          borderRadius: 3,
          backgroundColor: 'rgba(255,255,255,0.1)',
          '& .MuiLinearProgress-bar': {
            backgroundColor: color,
            borderRadius: 3,
          },
        }}
      />
      <Typography
        variant="caption"
        sx={{ color: 'text.secondary', width: 36, textAlign: 'right', fontFamily: 'monospace' }}
      >
        {score.toFixed(3)}
      </Typography>
    </Box>
  );
}

export function KpiCard({ label, value, sub, accent, icon }) {
  const accentColorMap = {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#eab308',
    low: '#22c55e',
    info: '#3b82f6',
    default: 'primary.main',
  };
  const accentColor = accentColorMap[accent || 'default'];
  return (
    <Paper
      sx={{
        p: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 0.5,
        border: '1px solid',
        borderColor: 'divider',
        height: '100%',
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography
          variant="caption"
          sx={{
            color: 'text.secondary',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            fontWeight: 500,
          }}
        >
          {label}
        </Typography>
        {icon}
      </Box>
      <Typography
        variant="h4"
        sx={{ color: accentColor, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}
      >
        {value}
      </Typography>
      {sub && (
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          {sub}
        </Typography>
      )}
    </Paper>
  );
}

export function EmptyState({ message }) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        py: 6,
        gap: 1,
      }}
    >
      <Box
        sx={{
          width: 40,
          height: 40,
          borderRadius: '50%',
          backgroundColor: 'action.hover',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Typography sx={{ color: 'text.secondary', fontSize: '1.25rem' }}>∅</Typography>
      </Box>
      <Typography variant="body2" sx={{ color: 'text.secondary' }}>
        {message}
      </Typography>
    </Box>
  );
}

/**
 * LoadingRows — skeleton rows for MUI Table.
 * Uses MUI TableRow/TableCell so it works inside <TableBody>.
 */
export function LoadingRows({ cols = 5, rows = 5 }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <TableRow key={i}>
          {Array.from({ length: cols }).map((__, j) => (
            <TableCell key={j}>
              <Box
                sx={{
                  height: 12,
                  borderRadius: 1,
                  backgroundColor: 'action.hover',
                }}
              />
            </TableCell>
          ))}
        </TableRow>
      ))}
    </>
  );
}

export function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}
