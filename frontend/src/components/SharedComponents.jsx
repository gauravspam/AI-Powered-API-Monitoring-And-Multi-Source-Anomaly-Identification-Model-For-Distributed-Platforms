import {
  Box,
  Chip,
  LinearProgress,
  Typography,
  Paper,
  TableRow,
  TableCell,
  useTheme,
} from '@mui/material';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { SEVERITY_COLORS } from '../theme';

// ─────────────────────────────────────────────────────────────────────────────
// SeverityBadge
// ─────────────────────────────────────────────────────────────────────────────
export function SeverityBadge({ severity }) {
  const s = (severity || 'NORMAL').toUpperCase();
  const color = SEVERITY_COLORS[s] || SEVERITY_COLORS.NORMAL;
  return (
    <Chip
      label={s}
      size="small"
      sx={{
        backgroundColor: `${color}20`,
        color,
        border: `1px solid ${color}40`,
        fontWeight: 600,
        fontSize: '0.6875rem',
        height: 22,
        letterSpacing: '0.03em',
        '& .MuiChip-label': { px: 1 },
      }}
    />
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// StatusDot
// ─────────────────────────────────────────────────────────────────────────────
const STATUS_DOT_COLORS = {
  healthy:      '#22c55e',
  online:       '#22c55e',
  active:       '#ef4444',
  degraded:     '#eab308',
  down:         '#ef4444',
  offline:      '#6b7280',
  acknowledged: '#eab308',
  resolved:     '#22c55e',
  unknown:      '#6b7280',
};

export function StatusDot({ status, size = 8 }) {
  const s = (status || '').toLowerCase();
  const color = STATUS_DOT_COLORS[s] || '#6b7280';
  return (
    <Box
      component="span"
      sx={{
        width: size,
        height: size,
        borderRadius: '50%',
        backgroundColor: color,
        display: 'inline-block',
        flexShrink: 0,
        boxShadow: s === 'active' || s === 'healthy' || s === 'online'
          ? `0 0 0 2px ${color}25`
          : 'none',
      }}
    />
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ScoreBar
// ─────────────────────────────────────────────────────────────────────────────
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
          height: 5,
          borderRadius: 3,
          backgroundColor: 'rgba(128,128,128,0.15)',
          '& .MuiLinearProgress-bar': { backgroundColor: color, borderRadius: 3 },
        }}
      />
      <Typography
        variant="caption"
        sx={{ color: 'text.secondary', width: 36, textAlign: 'right', fontFamily: 'monospace', fontSize: '0.7rem' }}
      >
        {score.toFixed(3)}
      </Typography>
    </Box>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// TrendSparkline — tiny inline line chart for KPI trend
// ─────────────────────────────────────────────────────────────────────────────
export function TrendSparkline({ data, color = 'hsl(188, 80%, 42%)', height = 32 }) {
  if (!data || data.length < 2) return null;
  const chartData = data.map((v, i) => ({ i, v }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
        <Line
          type="monotone"
          dataKey="v"
          stroke={color}
          strokeWidth={1.5}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// DeltaIndicator — arrow + % change
// ─────────────────────────────────────────────────────────────────────────────
export function DeltaIndicator({ delta, unit = '%', lowerIsBetter = false }) {
  if (delta === null || delta === undefined) return null;
  const isPositive = delta > 0;
  // For metrics like error rate, latency: higher = worse = red
  const isGood = lowerIsBetter ? !isPositive : isPositive;
  const color = delta === 0 ? '#6b7280' : isGood ? '#22c55e' : '#ef4444';

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25, color }}>
      {delta === 0 ? (
        <Minus size={11} />
      ) : isPositive ? (
        <TrendingUp size={11} />
      ) : (
        <TrendingDown size={11} />
      )}
      <Typography variant="caption" sx={{ color, fontSize: '0.7rem', fontVariantNumeric: 'tabular-nums' }}>
        {delta > 0 ? '+' : ''}{typeof delta === 'number' ? delta.toFixed(1) : delta}{unit}
      </Typography>
    </Box>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// KpiCard — enhanced with optional sparkline + delta
// ─────────────────────────────────────────────────────────────────────────────
const ACCENT_COLORS = {
  critical: '#ef4444',
  high:     '#f97316',
  medium:   '#eab308',
  low:      '#22c55e',
  info:     '#3b82f6',
  purple:   '#a855f7',
  default:  'hsl(188, 80%, 42%)',
};

export function KpiCard({
  label,
  value,
  sub,
  accent,
  icon: Icon,
  delta,
  deltaUnit = '%',
  lowerIsBetter = false,
  sparkData,
  sparkColor,
  highlight = false,
}) {
  const theme = useTheme();
  const accentColor = ACCENT_COLORS[accent || 'default'];
  const borderColor = highlight
    ? `${accentColor}60`
    : theme.palette.divider;

  return (
    <Paper
      elevation={0}
      sx={{
        p: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 0.5,
        border: '1px solid',
        borderColor,
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        transition: 'border-color 0.2s, box-shadow 0.2s',
        '&:hover': {
          borderColor: `${accentColor}80`,
          boxShadow: `0 0 0 1px ${accentColor}20`,
        },
      }}
    >
      {/* Accent bar top */}
      {highlight && (
        <Box sx={{
          position: 'absolute',
          top: 0, left: 0, right: 0,
          height: 2,
          backgroundColor: accentColor,
        }} />
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Typography variant="caption" sx={{
          color: 'text.secondary',
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
          fontWeight: 600,
          fontSize: '0.6rem',
          lineHeight: 1.4,
        }}>
          {label}
        </Typography>
        {Icon && (
          <Box sx={{ color: accentColor, opacity: 0.7, flexShrink: 0 }}>
            <Icon size={13} />
          </Box>
        )}
      </Box>

      <Typography variant="h5" sx={{
        color: accentColor,
        fontWeight: 700,
        fontVariantNumeric: 'tabular-nums lining-nums',
        lineHeight: 1.1,
        mt: 0.25,
      }}>
        {value}
      </Typography>

      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 'auto', pt: 0.5 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}>
          {sub && (
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
              {sub}
            </Typography>
          )}
          {delta !== undefined && (
            <DeltaIndicator delta={delta} unit={deltaUnit} lowerIsBetter={lowerIsBetter} />
          )}
        </Box>
        {sparkData && sparkData.length >= 2 && (
          <Box sx={{ width: 60, flexShrink: 0 }}>
            <TrendSparkline data={sparkData} color={sparkColor || accentColor} height={28} />
          </Box>
        )}
      </Box>
    </Paper>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// EmptyState
// ─────────────────────────────────────────────────────────────────────────────
export function EmptyState({ message, icon }) {
  return (
    <Box sx={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      py: 6,
      gap: 1.5,
    }}>
      <Box sx={{
        width: 40,
        height: 40,
        borderRadius: '50%',
        backgroundColor: 'action.hover',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <Typography sx={{ color: 'text.secondary', fontSize: '1.1rem' }}>{icon || '∅'}</Typography>
      </Box>
      <Typography variant="body2" sx={{ color: 'text.secondary' }}>
        {message}
      </Typography>
    </Box>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// LoadingRows — skeleton rows for MUI Table
// ─────────────────────────────────────────────────────────────────────────────
export function LoadingRows({ cols = 5, rows = 5 }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <TableRow key={i}>
          {Array.from({ length: cols }).map((__, j) => (
            <TableCell key={j}>
              <Box sx={{
                height: 11,
                borderRadius: 1,
                backgroundColor: 'action.hover',
                width: j === 0 ? '70%' : j === cols - 1 ? '40%' : '60%',
              }} />
            </TableCell>
          ))}
        </TableRow>
      ))}
    </>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// MonoCell — monospace table cell for IDs, service names, endpoints
// ─────────────────────────────────────────────────────────────────────────────
export function MonoCell({ children, color = 'primary.main', maxWidth, sx = {} }) {
  return (
    <TableCell sx={{
      fontFamily: 'monospace',
      fontSize: '0.75rem',
      color,
      maxWidth,
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap',
      ...sx,
    }}>
      {children}
    </TableCell>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SectionHeader — card header row with title + optional right content
// ─────────────────────────────────────────────────────────────────────────────
export function SectionHeader({ title, right, sx = {} }) {
  return (
    <Box sx={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      p: 2,
      borderBottom: '1px solid',
      borderColor: 'divider',
      ...sx,
    }}>
      <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary' }}>
        {title}
      </Typography>
      {right}
    </Box>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// FilterBar — common filter row wrapper
// ─────────────────────────────────────────────────────────────────────────────
export function FilterBar({ children }) {
  return (
    <Box sx={{
      display: 'flex',
      gap: 1.5,
      alignItems: 'center',
      flexWrap: 'wrap',
      p: 1.5,
      backgroundColor: 'action.hover',
      borderRadius: 2,
      border: '1px solid',
      borderColor: 'divider',
    }}>
      {children}
    </Box>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// timeAgo
// ─────────────────────────────────────────────────────────────────────────────
export function timeAgo(iso) {
  if (!iso) return '—';
  const diff = Date.now() - new Date(iso).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60)  return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60)  return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24)  return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

// ─────────────────────────────────────────────────────────────────────────────
// formatMs — human latency
// ─────────────────────────────────────────────────────────────────────────────
export function formatMs(ms) {
  if (!ms && ms !== 0) return '—';
  if (ms >= 1000) return `${(ms / 1000).toFixed(2)}s`;
  return `${Math.round(ms)}ms`;
}

// ─────────────────────────────────────────────────────────────────────────────
// ChartTooltip — shared Recharts tooltip
// ─────────────────────────────────────────────────────────────────────────────
export function ChartTooltip({ active, payload, label }) {
  if (!active || !Array.isArray(payload) || !payload.length) return null;
  return (
    <Paper sx={{ p: 1.5, border: '1px solid', borderColor: 'divider', minWidth: 120 }}>
      {label && (
        <Typography variant="caption" sx={{ color: 'text.secondary', mb: 0.5, display: 'block' }}>
          {label}
        </Typography>
      )}
      {payload.map((p) => (
        <Typography
          key={p.dataKey}
          variant="caption"
          sx={{ display: 'block', color: p.color || 'text.primary', fontVariantNumeric: 'tabular-nums' }}
        >
          {p.name || p.dataKey}:{' '}
          {typeof p.value === 'number'
            ? p.dataKey?.toLowerCase().includes('rate')
              ? (p.value * 100).toFixed(2) + '%'
              : p.dataKey?.toLowerCase().includes('latency') || p.dataKey?.toLowerCase().includes('ms')
              ? p.value.toLocaleString() + 'ms'
              : p.value.toLocaleString()
            : p.value}
        </Typography>
      ))}
    </Paper>
  );
}
