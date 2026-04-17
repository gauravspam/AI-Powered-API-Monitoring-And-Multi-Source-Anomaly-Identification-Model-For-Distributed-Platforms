import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  ToggleButtonGroup,
  ToggleButton,
  InputAdornment,
} from '@mui/material';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Search as SearchIcon } from 'lucide-react';
import { BACKEND_URL } from '@/api/http';
import { timeAgo, EmptyState } from '@/components/SharedComponents';

const proxyOrMock = async (path, mockFn) => {
  try {
    const resp = await fetch(`${BACKEND_URL}${path}`, { signal: AbortSignal.timeout(5000) });
    if (!resp.ok) throw new Error('Backend error');
    return await resp.json();
  } catch {
    return mockFn();
  }
};

const generateMockTraces = () => {
  const services = ['api-gateway', 'payment-service', 'user-service', 'auth-service'];
  const operations = ['GET /api/health', 'POST /payment/process', 'GET /api/users', 'POST /auth/login'];
  return Array.from({ length: 30 }, (_, i) => ({
    id: i + 1,
    traceId: `trace-${Math.random().toString(36).substr(2, 9)}`,
    spanId: `span-${i}`,
    serviceName: services[i % 4],
    operationName: operations[i % 4],
    durationMs: Math.floor(50 + Math.random() * 2000),
    statusCode: i % 5 === 0 ? 500 : i % 7 === 0 ? 429 : 200,
    timestamp: new Date(Date.now() - i * 120000).toISOString(),
    tags: { env: 'production', version: '1.0.0' },
    _mock: true,
  }));
};

const statusColor = (code) =>
  code >= 500 ? '#ef4444' : code >= 400 ? '#f97316' : '#22c55e';

export const Traces = () => {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const { data: tracesRaw, isLoading } = useQuery({
    queryKey: ['/api/proxy/traces'],
    queryFn: () => proxyOrMock('/api/traces/recent?page=0&size=30', generateMockTraces),
    refetchInterval: 20000,
  });

  const traces = Array.isArray(tracesRaw) ? tracesRaw : (tracesRaw?.content || []);

  const filtered = traces.filter((t) => {
    const matchSearch =
      !search ||
      t.traceId?.toLowerCase().includes(search.toLowerCase()) ||
      t.serviceName?.toLowerCase().includes(search.toLowerCase()) ||
      t.operationName?.toLowerCase().includes(search.toLowerCase());
    const is5xx = t.statusCode >= 500;
    const matchStatus =
      statusFilter === 'all' ||
      (statusFilter === 'error' && is5xx) ||
      (statusFilter === 'success' && !is5xx);
    return matchSearch && matchStatus;
  });

  const sorted = [...traces].sort((a, b) => a.durationMs - b.durationMs);
  const p50 = traces.length ? sorted[Math.floor(traces.length * 0.5)]?.durationMs : 0;
  const p99 = traces.length ? sorted[Math.floor(traces.length * 0.99)]?.durationMs : 0;
  const errorCount = traces.filter((t) => t.statusCode >= 400).length;
  const avgDuration = traces.length
    ? Math.round(traces.reduce((s, t) => s + t.durationMs, 0) / traces.length)
    : 0;

  const scatterData = traces.map((t, i) => ({
    x: i,
    y: t.durationMs,
    statusCode: t.statusCode,
    name: t.serviceName,
  }));

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
      {/* KPI row */}
      <Box sx={{ display: 'flex', gap: 2 }}>
        {[
          { label: 'Total Spans',  value: traces.length,       color: 'text.primary'  },
          { label: 'Avg Duration', value: `${avgDuration}ms`,  color: 'text.primary'  },
          { label: 'P99 Latency',  value: `${p99}ms`,          color: 'warning.main'  },
          { label: 'Error Spans',  value: errorCount,          color: 'error.main'    },
        ].map(({ label, value, color }) => (
          <Box
            key={label}
            sx={{ flex: 1, textAlign: 'center', p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}
          >
            <Typography variant="h5" sx={{ fontWeight: 600, color }}>
              {value}
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              {label}
            </Typography>
          </Box>
        ))}
      </Box>

      {/* Scatter chart */}
      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            Span Latency Distribution
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, fontSize: '0.75rem', color: 'text.secondary' }}>
            {[
              { label: '2xx', color: '#22c55e' },
              { label: '4xx', color: '#f97316' },
              { label: '5xx', color: '#ef4444' },
            ].map(({ label, color }) => (
              <Box key={label} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: color }} />
                <span>{label}</span>
              </Box>
            ))}
          </Box>
        </Box>
        {isLoading ? (
          <Box sx={{ height: 160, bgcolor: 'action.hover', borderRadius: 1 }} />
        ) : (
          <ResponsiveContainer width="100%" height={160}>
            <ScatterChart margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2a38" />
              <XAxis
                dataKey="x"
                tick={false}
                axisLine={false}
                tickLine={false}
                label={{ value: 'Span index', position: 'insideBottom', fontSize: 10, fill: '#6b7280' }}
              />
              <YAxis
                tick={{ fontSize: 10, fill: '#6b7280' }}
                tickLine={false}
                axisLine={false}
                width={45}
                unit="ms"
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload?.[0]) {
                    const d = payload[0].payload;
                    return (
                      <Paper sx={{ p: 1, border: '1px solid', borderColor: 'divider' }}>
                        <Typography variant="caption" sx={{ color: 'primary.main', display: 'block' }}>
                          {d.name}
                        </Typography>
                        <Typography variant="caption" sx={{ display: 'block' }}>
                          {d.y}ms
                        </Typography>
                        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                          HTTP {d.statusCode}
                        </Typography>
                      </Paper>
                    );
                  }
                  return null;
                }}
              />
              <Scatter
                data={scatterData}
                fill="#22c55e"
                shape={(props) => {
                  const { cx, cy, payload } = props;
                  return (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={3.5}
                      fill={statusColor(payload.statusCode)}
                      opacity={0.8}
                    />
                  );
                }}
              />
            </ScatterChart>
          </ResponsiveContainer>
        )}
      </Paper>

      {/* Filters */}
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
        <TextField
          placeholder="Search trace ID, service, operation…"
          size="small"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon size={18} style={{ color: '#6b7280' }} />
              </InputAdornment>
            ),
          }}
          sx={{ minWidth: 280 }}
        />
        <ToggleButtonGroup
          value={statusFilter}
          exclusive
          onChange={(e, v) => v && setStatusFilter(v)}
          size="small"
        >
          <ToggleButton value="all">All</ToggleButton>
          <ToggleButton value="success">Success</ToggleButton>
          <ToggleButton value="error">Error</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Table */}
      <Paper>
        <TableContainer sx={{ maxHeight: 'calc(100dvh - 500px)' }}>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 500, fontSize: '0.75rem' }}>Trace ID</TableCell>
                <TableCell sx={{ fontWeight: 500, fontSize: '0.75rem' }}>Service</TableCell>
                <TableCell sx={{ fontWeight: 500, fontSize: '0.75rem' }}>Operation</TableCell>
                <TableCell align="right" sx={{ fontWeight: 500, fontSize: '0.75rem' }}>Duration</TableCell>
                <TableCell align="right" sx={{ fontWeight: 500, fontSize: '0.75rem' }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 500, fontSize: '0.75rem' }}>Time</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 6 }).map((__, j) => (
                      <TableCell key={j}>
                        <Box sx={{ height: 12, bgcolor: 'action.hover', borderRadius: 1 }} />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6}>
                    <EmptyState message="No traces found" />
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((t, i) => (
                  <TableRow key={`${t.traceId}-${i}`} sx={{ '&:hover': { bgcolor: 'action.hover' } }}>
                    <TableCell
                      sx={{
                        fontSize: '0.75rem',
                        color: 'text.secondary',
                        maxWidth: 120,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        fontFamily: 'monospace',
                      }}
                    >
                      {t.traceId}
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.75rem', color: 'primary.main' }}>
                      {t.serviceName}
                    </TableCell>
                    <TableCell
                      sx={{ fontSize: '0.75rem', maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis' }}
                    >
                      {t.operationName}
                    </TableCell>
                    <TableCell
                      align="right"
                      sx={{
                        fontSize: '0.75rem',
                        color:
                          t.durationMs > 1000 ? 'warning.main' :
                          t.durationMs > 500  ? '#eab308' :
                          'text.primary',
                      }}
                    >
                      {t.durationMs}ms
                    </TableCell>
                    <TableCell
                      align="right"
                      sx={{ fontSize: '0.75rem', fontWeight: 600, color: statusColor(t.statusCode) }}
                    >
                      {t.statusCode}
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.75rem', color: 'text.secondary', fontFamily: 'monospace' }}>
                      {timeAgo(t.timestamp)}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default Traces;
