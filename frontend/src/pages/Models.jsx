import { useQuery } from '@tanstack/react-query';
import { Box, Paper, Typography, LinearProgress } from '@mui/material';
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { BACKEND_URL } from '@/api/http';
import { StatusDot, EmptyState } from '@/components/SharedComponents';

const proxyOrMock = async (path, mockFn) => {
  try {
    const resp = await fetch(`${BACKEND_URL}${path}`, { signal: AbortSignal.timeout(5000) });
    if (!resp.ok) throw new Error('Backend error');
    return await resp.json();
  } catch {
    return mockFn();
  }
};

const generateMockModels = () => [
  {
    id: 1, name: 'MSIF-LSTM', version: '1.0.0', type: 'LSTM',
    status: 'online', latencyMs: 45, throughputPerSec: 220,
    accuracy: 94.2, f1Score: 0.921, precision: 0.935, recall: 0.908,
    lastRetrainAt: '2026-04-08T10:00:00Z',
  },
  {
    id: 2, name: 'PLE-GRU', version: '1.0.0', type: 'GRU',
    status: 'online', latencyMs: 38, throughputPerSec: 285,
    accuracy: 91.7, f1Score: 0.894, precision: 0.912, recall: 0.877,
    lastRetrainAt: '2026-04-08T10:00:00Z',
  },
  {
    id: 3, name: 'Hybrid Ensemble', version: '1.0.0', type: 'Ensemble',
    status: 'online', latencyMs: 82, throughputPerSec: 195,
    accuracy: 96.1, f1Score: 0.948, precision: 0.961, recall: 0.936,
    lastRetrainAt: '2026-04-08T10:00:00Z',
  },
];

const MODEL_COLORS = {
  'MSIF-LSTM':       'hsl(188, 80%, 42%)',
  'PLE-GRU':         '#f97316',
  'Hybrid Ensemble': '#a855f7',
};

const MODEL_ARCH = {
  'MSIF-LSTM': [
    'Multi-Scale Isolation Forest + LSTM',
    'Window: 60 timesteps · 5 features',
    'Embedding dim: 3 · Hidden: 64',
    'MSIF weight: 0.60 in ensemble',
  ],
  'PLE-GRU': [
    'Probabilistic Label Enhancement + GRU',
    'Window: 1440 timesteps · 7 features',
    'Experts: 4 · Hidden: 128',
    'PLE weight: 0.40 in ensemble',
  ],
  'Hybrid Ensemble': [
    'Weighted combination of MSIF-LSTM + PLE-GRU',
    'Fusion: weighted_ensemble / rule_based_fallback',
    'Threshold: 0.70',
    'Confidence scaled by modality count',
  ],
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && Array.isArray(payload) && payload.length) {
    return (
      <Box sx={{ p: 1.5, border: '1px solid', borderColor: 'divider', bgcolor: 'background.paper', borderRadius: 1 }}>
        <Typography variant="caption" sx={{ color: 'text.secondary', mb: 0.5, display: 'block', fontWeight: 500 }}>
          {label}
        </Typography>
        {payload.map((p) => (
          <Typography
            key={p.dataKey}
            variant="caption"
            sx={{ display: 'block', color: p.color, fontVariantNumeric: 'tabular-nums' }}
          >
            {p.dataKey}: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}
          </Typography>
        ))}
      </Box>
    );
  }
  return null;
};

export const Models = () => {
  const { data: models, isLoading } = useQuery({
    queryKey: ['/api/proxy/models'],
    queryFn: () => proxyOrMock('/api/models', generateMockModels),
    refetchInterval: 60000,
  });

  const modelList = Array.isArray(models) ? models : [];

  const comparisonData = [
    { metric: 'Accuracy',  ...Object.fromEntries(modelList.map((m) => [m.name, m.accuracy])) },
    { metric: 'F1 Score',  ...Object.fromEntries(modelList.map((m) => [m.name, +(m.f1Score * 100).toFixed(1)])) },
    { metric: 'Precision', ...Object.fromEntries(modelList.map((m) => [m.name, +(m.precision * 100).toFixed(1)])) },
    { metric: 'Recall',    ...Object.fromEntries(modelList.map((m) => [m.name, +(m.recall * 100).toFixed(1)])) },
  ];

  const radarData = [
    { axis: 'Accuracy',   ...Object.fromEntries(modelList.map((m) => [m.name, m.accuracy])) },
    { axis: 'F1',         ...Object.fromEntries(modelList.map((m) => [m.name, +(m.f1Score * 100).toFixed(1)])) },
    { axis: 'Precision',  ...Object.fromEntries(modelList.map((m) => [m.name, +(m.precision * 100).toFixed(1)])) },
    { axis: 'Recall',     ...Object.fromEntries(modelList.map((m) => [m.name, +(m.recall * 100).toFixed(1)])) },
    { axis: 'Throughput', ...Object.fromEntries(modelList.map((m) => [m.name, Math.min(m.throughputPerSec / 3, 100)])) },
    { axis: 'Speed',      ...Object.fromEntries(modelList.map((m) => [m.name, Math.min(100 - m.latencyMs / 1.5, 100)])) },
  ];

  const perfData = modelList.map((m) => ({
    name: m.name,
    latency: m.latencyMs,
    throughput: m.throughputPerSec,
  }));

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {[1, 2, 3].map((i) => (
          <Paper key={i} sx={{ p: 3, height: 128 }} />
        ))}
      </Box>
    );
  }

  if (!modelList.length) return <EmptyState message="No model data available" />;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Model cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 3 }}>
        {modelList.map((m) => (
          <Paper key={m.id} sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <Box>
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  {m.name}
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  v{m.version} · {m.type}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <StatusDot status={m.status} />
                <Typography variant="caption" sx={{ textTransform: 'capitalize', color: 'text.secondary' }}>
                  {m.status}
                </Typography>
              </Box>
            </Box>

            {/* Metrics 2×2 grid */}
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 1.5, mb: 1 }}>
              {[
                { label: 'Accuracy',  value: m.accuracy  ? `${m.accuracy.toFixed(1)}%`  : '—' },
                { label: 'F1 Score',  value: m.f1Score   ? m.f1Score.toFixed(3)          : '—' },
                { label: 'Precision', value: m.precision ? m.precision.toFixed(3)        : '—' },
                { label: 'Recall',    value: m.recall    ? m.recall.toFixed(3)           : '—' },
              ].map(({ label, value }) => (
                <Box key={label} sx={{ p: 1, borderRadius: 1, bgcolor: 'action.hover' }}>
                  <Typography
                    variant="caption"
                    sx={{
                      color: 'text.secondary',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      fontSize: '0.625rem',
                    }}
                  >
                    {label}
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, mt: 0.5 }}>
                    {value}
                  </Typography>
                </Box>
              ))}
            </Box>

            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '0.75rem',
                color: 'text.secondary',
                pt: 1,
                borderTop: '1px solid',
                borderColor: 'divider',
              }}
            >
              <span>
                P50 latency:{' '}
                <span style={{ color: 'inherit', fontVariantNumeric: 'tabular-nums' }}>
                  {m.latencyMs || '—'}ms
                </span>
              </span>
              <span>
                Throughput:{' '}
                <span style={{ color: 'inherit', fontVariantNumeric: 'tabular-nums' }}>
                  {m.throughputPerSec || '—'}/s
                </span>
              </span>
            </Box>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.625rem' }}>
              Last retrained: {new Date(m.lastRetrainAt).toLocaleDateString()}
            </Typography>
          </Paper>
        ))}
      </Box>

      {/* Charts row */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: 3 }}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="body2" sx={{ fontWeight: 600, mb: 2 }}>
            Performance Radar
          </Typography>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData} margin={{ top: 8, right: 16, bottom: 8, left: 16 }}>
              <PolarGrid stroke="#1e2a38" />
              <PolarAngleAxis dataKey="axis" tick={{ fontSize: 10, fill: '#6b7280' }} />
              {modelList.map((m) => (
                <Radar
                  key={m.name}
                  name={m.name}
                  dataKey={m.name}
                  stroke={MODEL_COLORS[m.name] || '#6b7280'}
                  fill={MODEL_COLORS[m.name] || '#6b7280'}
                  fillOpacity={0.1}
                  strokeWidth={1.5}
                />
              ))}
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
            </RadarChart>
          </ResponsiveContainer>
        </Paper>
        <Paper sx={{ p: 2 }}>
          <Typography variant="body2" sx={{ fontWeight: 600, mb: 2 }}>
            Metrics Comparison
          </Typography>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={comparisonData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2a38" vertical={false} />
              <XAxis dataKey="metric" tick={{ fontSize: 10, fill: '#6b7280' }} tickLine={false} axisLine={false} />
              <YAxis
                tick={{ fontSize: 10, fill: '#6b7280' }}
                tickLine={false}
                axisLine={false}
                domain={[80, 100]}
                width={32}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
              {modelList.map((m) => (
                <Bar
                  key={m.name}
                  dataKey={m.name}
                  fill={MODEL_COLORS[m.name] || '#6b7280'}
                  radius={[3, 3, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      </Box>

      {/* Latency vs Throughput bars */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="body2" sx={{ fontWeight: 600, mb: 2 }}>
          Latency vs Throughput
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2 }}>
          {perfData.map((p) => (
            <Box
              key={p.name}
              sx={{ p: 2, borderRadius: 1, bgcolor: 'action.hover', display: 'flex', flexDirection: 'column', gap: 1.5 }}
            >
              <Typography variant="body2" sx={{ fontWeight: 600, color: MODEL_COLORS[p.name] || '#6b7280' }}>
                {p.name}
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>Latency</Typography>
                    <Typography variant="caption" sx={{ fontVariantNumeric: 'tabular-nums' }}>{p.latency}ms</Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={Math.min(p.latency / 1.5, 100)}
                    sx={{
                      height: 6,
                      borderRadius: 3,
                      bgcolor: 'background.default',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: MODEL_COLORS[p.name] || '#6b7280',
                        opacity: 0.7,
                      },
                    }}
                  />
                </Box>
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>Throughput</Typography>
                    <Typography variant="caption" sx={{ fontVariantNumeric: 'tabular-nums' }}>{p.throughput}/s</Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={Math.min(p.throughput / 3, 100)}
                    sx={{
                      height: 6,
                      borderRadius: 3,
                      bgcolor: 'background.default',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: MODEL_COLORS[p.name] || '#6b7280',
                      },
                    }}
                  />
                </Box>
              </Box>
            </Box>
          ))}
        </Box>
      </Paper>

      {/* Architecture notes */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2 }}>
        {modelList.map((m) => (
          <Box key={m.name} sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            <Typography variant="body1" sx={{ fontWeight: 600, color: MODEL_COLORS[m.name] }}>
              {m.name}
            </Typography>
            {(MODEL_ARCH[m.name] || []).map((line) => (
              <Typography key={line} variant="caption" sx={{ color: 'text.secondary' }}>
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
