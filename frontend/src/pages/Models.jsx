import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box, Paper, Typography, LinearProgress, ToggleButtonGroup, ToggleButton,
  MenuItem, Select, FormControl, InputLabel, Chip, useTheme,
} from '@mui/material';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from 'recharts';
import { Cpu, AlertTriangle, CheckCircle } from 'lucide-react';
import { BACKEND_URL } from '@/api/http';
import { StatusDot, EmptyState, KpiCard, FilterBar, ChartTooltip } from '@/components/SharedComponents';
import { MODEL_COLORS } from '@/theme';

const proxyOrMock = async (path, mockFn) => {
  try {
    const r = await fetch(`${BACKEND_URL}${path}`, { signal: AbortSignal.timeout(5000) });
    if (!r.ok) throw new Error();
    return r.json();
  } catch {
    return mockFn();
  }
};

const generateMockModels = () => [
  {
    id: 1, name: 'MSIF-LSTM', version: '1.0.0', type: 'LSTM',
    status: 'online',
    latencyMs: 45, throughputPerSec: 220,
    accuracy: 94.2, f1Score: 0.921, precision: 0.935, recall: 0.908,
    lastRetrainAt: '2026-04-08T10:00:00Z',
    confidenceDrift: -0.012,  // negative = drifting down
    inferenceLast24h: 18400,
  },
  {
    id: 2, name: 'PLE-GRU', version: '1.0.0', type: 'GRU',
    status: 'online',
    latencyMs: 38, throughputPerSec: 285,
    accuracy: 91.7, f1Score: 0.894, precision: 0.912, recall: 0.877,
    lastRetrainAt: '2026-04-08T10:00:00Z',
    confidenceDrift: +0.003,
    inferenceLast24h: 22100,
  },
  {
    id: 3, name: 'Hybrid Ensemble', version: '1.0.0', type: 'Ensemble',
    status: 'online',
    latencyMs: 82, throughputPerSec: 195,
    accuracy: 96.1, f1Score: 0.948, precision: 0.961, recall: 0.936,
    lastRetrainAt: '2026-04-08T10:00:00Z',
    confidenceDrift: -0.005,
    inferenceLast24h: 15900,
  },
];

const MODEL_ARCH = {
  'MSIF-LSTM': [
    'Multi-Scale Isolation Forest + LSTM',
    'Window: 60 timesteps · 5 features',
    'Embedding dim: 3 · Hidden: 64',
    'Ensemble weight: 0.60',
  ],
  'PLE-GRU': [
    'Probabilistic Label Enhancement + GRU',
    'Window: 1440 timesteps · 7 features',
    'Experts: 4 · Hidden: 128',
    'Ensemble weight: 0.40',
  ],
  'Hybrid Ensemble': [
    'Weighted combination: MSIF-LSTM + PLE-GRU',
    'Fusion: weighted_ensemble / rule_based_fallback',
    'Threshold: 0.70',
    'Confidence scaled by modality count',
  ],
};

export const Models = () => {
  const theme  = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const gridColor = isDark ? 'hsl(222, 14%, 16%)' : 'hsl(222, 14%, 88%)';
  const tickColor = isDark ? '#6b7280' : '#9ca3af';
  const polarGridColor = isDark ? 'hsl(222, 14%, 20%)' : 'hsl(222, 14%, 82%)';

  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter,   setTypeFilter]   = useState('all');

  const { data: models, isLoading } = useQuery({
    queryKey: ['/api/proxy/models'],
    queryFn: () => proxyOrMock('/api/models', generateMockModels),
    refetchInterval: 60000,
  });

  const modelList = useMemo(() =>
    (Array.isArray(models) ? models : []).filter((m) => {
      const matchStatus = statusFilter === 'all' || m.status === statusFilter;
      const matchType   = typeFilter   === 'all' || m.type   === typeFilter;
      return matchStatus && matchType;
    }), [models, statusFilter, typeFilter]);

  const allModels = Array.isArray(models) ? models : [];
  const types = [...new Set(allModels.map((m) => m.type).filter(Boolean))];

  const onlineCount  = allModels.filter((m) => m.status === 'online').length;
  const offlineCount = allModels.filter((m) => m.status !== 'online').length;

  const comparisonData = [
    { metric: 'Accuracy',  ...Object.fromEntries(modelList.map((m) => [m.name, m.accuracy])) },
    { metric: 'F1',        ...Object.fromEntries(modelList.map((m) => [m.name, +(m.f1Score  * 100).toFixed(1)])) },
    { metric: 'Precision', ...Object.fromEntries(modelList.map((m) => [m.name, +(m.precision * 100).toFixed(1)])) },
    { metric: 'Recall',    ...Object.fromEntries(modelList.map((m) => [m.name, +(m.recall    * 100).toFixed(1)])) },
  ];

  const radarData = [
    { axis: 'Accuracy',   ...Object.fromEntries(modelList.map((m) => [m.name, m.accuracy])) },
    { axis: 'F1',         ...Object.fromEntries(modelList.map((m) => [m.name, +(m.f1Score  * 100).toFixed(1)])) },
    { axis: 'Precision',  ...Object.fromEntries(modelList.map((m) => [m.name, +(m.precision * 100).toFixed(1)])) },
    { axis: 'Recall',     ...Object.fromEntries(modelList.map((m) => [m.name, +(m.recall    * 100).toFixed(1)])) },
    { axis: 'Throughput', ...Object.fromEntries(modelList.map((m) => [m.name, Math.min(m.throughputPerSec / 3, 100)])) },
    { axis: 'Speed',      ...Object.fromEntries(modelList.map((m) => [m.name, Math.min(100 - m.latencyMs / 1.5, 100)])) },
  ];

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {[1, 2, 3].map((i) => <Paper key={i} sx={{ p: 3, height: 140 }} />)}
      </Box>
    );
  }

  if (!allModels.length) return <EmptyState message="No model data available" />;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
      {/* Summary KPIs */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 1.5 }}>
        <KpiCard label="Models Online"  value={onlineCount}  sub="Serving predictions" accent="low"    icon={Cpu} />
        <KpiCard label="Models Offline" value={offlineCount} sub="Not responding"       accent={offlineCount > 0 ? 'critical' : 'low'} icon={Cpu} highlight={offlineCount > 0} />
        <KpiCard label="Best Accuracy"  value={allModels.length ? `${Math.max(...allModels.map((m) => m.accuracy)).toFixed(1)}%` : '—'} sub="Hybrid Ensemble" accent="default" icon={CheckCircle} />
        <KpiCard label="Fastest Model"  value={allModels.length ? `${Math.min(...allModels.map((m) => m.latencyMs))}ms` : '—'} sub="Inference latency" accent="info" icon={Cpu} />
      </Box>

      {/* Filters */}
      <FilterBar>
        {/* Status filter */}
        <ToggleButtonGroup value={statusFilter} exclusive onChange={(_, v) => v && setStatusFilter(v)} size="small">
          <ToggleButton value="all">All</ToggleButton>
          <ToggleButton value="online"  sx={{ '&.Mui-selected': { color: '#22c55e' } }}>Online</ToggleButton>
          <ToggleButton value="offline" sx={{ '&.Mui-selected': { color: '#6b7280' } }}>Offline</ToggleButton>
        </ToggleButtonGroup>

        {/* Model type filter */}
        <FormControl size="small" sx={{ minWidth: 130 }}>
          <InputLabel sx={{ fontSize: '0.8rem' }}>Model Type</InputLabel>
          <Select
            value={typeFilter}
            label="Model Type"
            onChange={(e) => setTypeFilter(e.target.value)}
            sx={{ fontSize: '0.8rem' }}
          >
            <MenuItem value="all" sx={{ fontSize: '0.8rem' }}>All Types</MenuItem>
            {types.map((t) => (
              <MenuItem key={t} value={t} sx={{ fontSize: '0.8rem' }}>{t}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </FilterBar>

      {/* Model cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 2 }}>
        {modelList.map((m) => {
          const modelColor = MODEL_COLORS[m.name] || '#6b7280';
          const isDrifting = m.confidenceDrift !== null && m.confidenceDrift < -0.01;
          return (
            <Paper key={m.id} elevation={0} sx={{
              p: 2.5, display: 'flex', flexDirection: 'column', gap: 2,
              border: '1px solid',
              borderColor: isDrifting ? '#f9731640' : 'divider',
              borderTop: `3px solid ${modelColor}`,
            }}>
              {/* Header */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography variant="body1" sx={{ fontWeight: 700, color: modelColor }}>
                    {m.name}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    v{m.version} · {m.type}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                  <StatusDot status={m.status} />
                  <Typography variant="caption" sx={{ textTransform: 'capitalize', color: 'text.secondary' }}>
                    {m.status}
                  </Typography>
                </Box>
              </Box>

              {/* Confidence drift indicator */}
              {m.confidenceDrift !== null && (
                <Box sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.75,
                  px: 1,
                  py: 0.5,
                  borderRadius: 1,
                  backgroundColor: isDrifting ? 'rgba(249,115,22,0.1)' : 'rgba(34,197,94,0.08)',
                  border: '1px solid',
                  borderColor: isDrifting ? '#f9731630' : '#22c55e30',
                }}>
                  {isDrifting ? (
                    <AlertTriangle size={12} style={{ color: '#f97316', flexShrink: 0 }} />
                  ) : (
                    <CheckCircle size={12} style={{ color: '#22c55e', flexShrink: 0 }} />
                  )}
                  <Typography variant="caption" sx={{ color: isDrifting ? '#f97316' : '#22c55e', fontSize: '0.7rem' }}>
                    Confidence drift:{' '}
                    <span style={{ fontFamily: 'monospace' }}>
                      {m.confidenceDrift > 0 ? '+' : ''}{(m.confidenceDrift * 100).toFixed(1)}%
                    </span>
                    {isDrifting && ' — retraining recommended'}
                  </Typography>
                </Box>
              )}

              {/* Metrics 2×2 */}
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 1 }}>
                {[
                  { label: 'Accuracy',  value: m.accuracy  ? `${m.accuracy.toFixed(1)}%`  : '—' },
                  { label: 'F1 Score',  value: m.f1Score   ? m.f1Score.toFixed(3)          : '—' },
                  { label: 'Precision', value: m.precision ? m.precision.toFixed(3)        : '—' },
                  { label: 'Recall',    value: m.recall    ? m.recall.toFixed(3)           : '—' },
                ].map(({ label, value }) => (
                  <Box key={label} sx={{ p: 1, borderRadius: 1, bgcolor: 'action.hover' }}>
                    <Typography variant="caption" sx={{
                      color: 'text.secondary',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      fontSize: '0.6rem',
                      fontWeight: 600,
                    }}>
                      {label}
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 700, mt: 0.25, fontVariantNumeric: 'tabular-nums' }}>
                      {value}
                    </Typography>
                  </Box>
                ))}
              </Box>

              {/* Latency + Throughput bars */}
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>Inference Latency</Typography>
                    <Typography variant="caption" sx={{ fontVariantNumeric: 'tabular-nums', fontSize: '0.7rem' }}>{m.latencyMs}ms</Typography>
                  </Box>
                  <LinearProgress variant="determinate" value={Math.min(m.latencyMs / 1.5, 100)}
                    sx={{
                      height: 5, borderRadius: 3, bgcolor: 'background.default',
                      '& .MuiLinearProgress-bar': { backgroundColor: modelColor, opacity: 0.7 },
                    }} />
                </Box>
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>Throughput</Typography>
                    <Typography variant="caption" sx={{ fontVariantNumeric: 'tabular-nums', fontSize: '0.7rem' }}>{m.throughputPerSec}/s</Typography>
                  </Box>
                  <LinearProgress variant="determinate" value={Math.min(m.throughputPerSec / 3, 100)}
                    sx={{
                      height: 5, borderRadius: 3, bgcolor: 'background.default',
                      '& .MuiLinearProgress-bar': { backgroundColor: modelColor },
                    }} />
                </Box>
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>Inferences (24h)</Typography>
                    <Typography variant="caption" sx={{ fontVariantNumeric: 'tabular-nums', fontSize: '0.7rem' }}>
                      {(m.inferenceLast24h || 0).toLocaleString()}
                    </Typography>
                  </Box>
                </Box>
              </Box>

              <Box sx={{ pt: 1, borderTop: '1px solid', borderColor: 'divider' }}>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.65rem' }}>
                  Last retrained: {new Date(m.lastRetrainAt).toLocaleDateString()}
                </Typography>
              </Box>
            </Paper>
          );
        })}
      </Box>

      {/* Charts row */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 2 }}>
        <Paper elevation={0} sx={{ p: 2, border: '1px solid', borderColor: 'divider' }}>
          <Typography variant="body2" sx={{ fontWeight: 600, mb: 2 }}>Performance Radar</Typography>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData} margin={{ top: 8, right: 20, bottom: 8, left: 20 }}>
              <PolarGrid stroke={polarGridColor} />
              <PolarAngleAxis dataKey="axis" tick={{ fontSize: 10, fill: tickColor }} />
              {modelList.map((m) => (
                <Radar
                  key={m.name}
                  name={m.name}
                  dataKey={m.name}
                  stroke={MODEL_COLORS[m.name] || '#6b7280'}
                  fill={MODEL_COLORS[m.name] || '#6b7280'}
                  fillOpacity={0.08}
                  strokeWidth={1.5}
                />
              ))}
              <Legend iconType="circle" iconSize={7} wrapperStyle={{ fontSize: '0.7rem' }} />
            </RadarChart>
          </ResponsiveContainer>
        </Paper>

        <Paper elevation={0} sx={{ p: 2, border: '1px solid', borderColor: 'divider' }}>
          <Typography variant="body2" sx={{ fontWeight: 600, mb: 2 }}>Metrics Comparison</Typography>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={comparisonData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
              <XAxis dataKey="metric" tick={{ fontSize: 10, fill: tickColor }} tickLine={false} axisLine={false} />
              <YAxis
                tick={{ fontSize: 10, fill: tickColor }}
                tickLine={false}
                axisLine={false}
                domain={[80, 100]}
                width={30}
              />
              <Tooltip content={<ChartTooltip />} />
              <Legend iconType="circle" iconSize={7} wrapperStyle={{ fontSize: '0.7rem' }} />
              {modelList.map((m) => (
                <Bar key={m.name} dataKey={m.name} fill={MODEL_COLORS[m.name] || '#6b7280'} radius={[3, 3, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      </Box>

      {/* Architecture notes */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 2 }}>
        {allModels.map((m) => (
          <Box key={m.name} sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}>
            <Typography variant="body2" sx={{ fontWeight: 700, color: MODEL_COLORS[m.name], mb: 1 }}>
              {m.name}
            </Typography>
            {(MODEL_ARCH[m.name] || []).map((line) => (
              <Typography key={line} variant="caption" sx={{ color: 'text.secondary', display: 'block', lineHeight: 1.6 }}>
                {line}
              </Typography>
            ))}
          </Box>
        ))}
      </Box>
    </Box>
  );
};

export default Models;
