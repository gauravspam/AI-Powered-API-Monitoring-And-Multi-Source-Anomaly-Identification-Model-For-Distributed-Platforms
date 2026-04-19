import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box, Paper, Typography, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, TextField, ToggleButtonGroup, ToggleButton,
  InputAdornment, MenuItem, Select, FormControl, InputLabel, useTheme,
} from '@mui/material';
import {
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Cell,
} from 'recharts';
import { Search, GitBranch } from 'lucide-react';
import { BACKEND_URL } from '@/api/http';
import { EmptyState, LoadingRows, KpiCard, FilterBar, timeAgo } from '@/components/SharedComponents';

const proxyOrMock = async (path, mockFn) => {
  try {
    const r = await fetch(`${BACKEND_URL}${path}`, { signal: AbortSignal.timeout(5000) });
    if (!r.ok) throw new Error();
    return r.json();
  } catch {
    const fallback = typeof mockFn === 'function' ? mockFn() : mockFn;
    return Array.isArray(fallback) ? [] : {};
  }
};

const generateMockTraces = () => {
  const services   = ['api-gateway', 'payment-service', 'user-service', 'auth-service', 'analytics-service'];
  const operations = ['GET /api/health', 'POST /payment/process', 'GET /api/users', 'POST /auth/login', 'GET /api/analytics'];
  return Array.from({ length: 40 }, (_, i) => ({
    id: i + 1,
    traceId: `trace-${Math.random().toString(36).substr(2, 9)}`,
    spanId: `span-${i}`,
    serviceName: services[i % services.length],
    operationName: operations[i % operations.length],
    durationMs: Math.floor(20 + Math.random() * 3000),
    statusCode: i % 5 === 0 ? 500 : i % 7 === 0 ? 429 : i % 11 === 0 ? 404 : 200,
    timestamp: new Date(Date.now() - i * 90000).toISOString(),
    _mock: true,
  }));
};

const normalizeTrace = (t, index) => {
  const durationMs =
    t.durationMs ??
    t.duration_ms ??
    t.duration ??
    0;

  return {
    id: t.id ?? index,
    traceId: t.traceId || t.trace_id || `trace-${index}`,
    spanId: t.spanId || t.span_id || `span-${index}`,
    serviceName: t.serviceName || t.service_name || 'unknown-service',
    operationName: t.operationName || t.operation_name || 'unknown-operation',
    durationMs,
    statusCode: t.statusCode ?? t.status_code ?? 200,
    timestamp: t.timestamp || t.startTime || t.start_time || new Date().toISOString(),
    _mock: t._mock,
  };
};

const DURATION_THRESHOLDS = [
  { label: 'All',    value: 0    },
  { label: '>100ms', value: 100  },
  { label: '>500ms', value: 500  },
  { label: '>1s',    value: 1000 },
  { label: '>2s',    value: 2000 },
];

const statusColor = (code) =>
  code >= 500 ? '#ef4444' :
  code >= 400 ? '#f97316' :
  '#22c55e';

const durationColor = (ms) => {
  if (ms > 2000) return '#ef4444';
  if (ms > 1000) return '#f97316';
  if (ms > 500)  return '#eab308';
  return undefined;
};

const percentile = (sorted, p) => {
  if (!sorted.length) return 0;
  const idx = Math.min(Math.floor(sorted.length * p), sorted.length - 1);
  return sorted[idx];
};

export const Traces = () => {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const gridColor = isDark ? 'hsl(222, 14%, 16%)' : 'hsl(222, 14%, 88%)';
  const tickColor = isDark ? '#6b7280' : '#9ca3af';

  const [search,    setSearch]    = useState('');
  const [statusFilter,   setStatusFilter]   = useState('all');
  const [serviceFilter,  setServiceFilter]  = useState('all');
  const [durationFilter, setDurationFilter] = useState(0);

  const { data: tracesRaw, isLoading } = useQuery({
    queryKey: ['/api/proxy/traces'],
    queryFn: () => proxyOrMock('/api/traces/recent?page=0&size=30', generateMockTraces),
    refetchInterval: 20000,
  });

  const traces = useMemo(() => {
    const raw = Array.isArray(tracesRaw) ? tracesRaw : (tracesRaw?.content || []);
    return raw.map((t, i) => normalizeTrace(t, i));
  }, [tracesRaw]);

  const services = useMemo(() => {
    const s = [...new Set(traces.map((t) => t.serviceName).filter(Boolean))].sort();
    return ['all', ...s];
  }, [traces]);

  const filtered = useMemo(() =>
    traces.filter((t) => {
      const matchSearch =
        !search ||
        t.traceId?.toLowerCase().includes(search.toLowerCase()) ||
        t.serviceName?.toLowerCase().includes(search.toLowerCase()) ||
        t.operationName?.toLowerCase().includes(search.toLowerCase());
      const matchStatus =
        statusFilter === 'all' ||
        (statusFilter === '2xx' && t.statusCode < 300 && t.statusCode >= 200) ||
        (statusFilter === '4xx' && t.statusCode >= 400 && t.statusCode < 500) ||
        (statusFilter === '5xx' && t.statusCode >= 500);
      const matchService  = serviceFilter  === 'all' || t.serviceName === serviceFilter;
      const matchDuration = durationFilter === 0     || t.durationMs  >= durationFilter;
      return matchSearch && matchStatus && matchService && matchDuration;
    }), [traces, search, statusFilter, serviceFilter, durationFilter]);

  // Percentile calculations
  const sortedDurations = useMemo(() => {
    const d = [...filtered].map((t) => t.durationMs).sort((a, b) => a - b);
    return d;
  }, [filtered]);

  const p50 = percentile(sortedDurations, 0.50);
  const p95 = percentile(sortedDurations, 0.95);
  const p99 = percentile(sortedDurations, 0.99);
  const errorCount  = filtered.filter((t) => t.statusCode >= 400).length;
  const errorRatePct = filtered.length ? ((errorCount / filtered.length) * 100).toFixed(1) : 0;

  const latencyHistogram = useMemo(() => {
    const buckets = [
      { range: '0-100ms', min: 0, max: 100, count: 0 },
      { range: '100-500ms', min: 100, max: 500, count: 0 },
      { range: '500ms-1s', min: 500, max: 1000, count: 0 },
      { range: '1s-2s', min: 1000, max: 2000, count: 0 },
      { range: '>2s', min: 2000, max: Infinity, count: 0 },
    ];
    filtered.forEach((t) => {
      const bucket = buckets.find((b) => t.durationMs >= b.min && t.durationMs < b.max);
      if (bucket) bucket.count++;
    });
    return buckets;
  }, [filtered]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
      {/* Latency percentile KPI row */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: 1.5 }}>
        <KpiCard label="P50 Latency" value={`${p50}ms`} sub="Median response time"  accent="low"    icon={GitBranch} />
        <KpiCard label="P95 Latency" value={`${p95}ms`} sub="95th percentile"        accent={p95 > 1000 ? 'high' : 'medium'} icon={GitBranch} />
        <KpiCard label="P99 Latency" value={`${p99}ms`} sub="Tail latency"           accent={p99 > 1000 ? 'critical' : 'high'} icon={GitBranch} highlight={p99 > 1000} />
        <KpiCard label="Total Spans" value={traces.length} sub="In current window"   accent="info"   icon={GitBranch} />
        <KpiCard label="Error Spans" value={errorCount}    sub={`${errorRatePct}% of all spans`} accent={errorCount > 0 ? 'critical' : 'low'} icon={GitBranch} highlight={errorCount > 0} />
      </Box>

      {/* Scatter chart */}
      <Paper elevation={0} sx={{ p: 2, border: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>Span Latency Distribution</Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            {[
              { label: '2xx', color: '#22c55e' },
              { label: '4xx', color: '#f97316' },
              { label: '5xx', color: '#ef4444' },
            ].map(({ label, color }) => (
              <Box key={label} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 7, height: 7, borderRadius: '50%', bgcolor: color }} />
                <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>{label}</Typography>
              </Box>
            ))}
          </Box>
        </Box>
        {isLoading ? (
          <Box sx={{ height: 160, bgcolor: 'action.hover', borderRadius: 1 }} />
        ) : (
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={latencyHistogram} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
              <XAxis
                dataKey="range"
                tick={{ fontSize: 10, fill: tickColor }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 10, fill: tickColor }}
                tickLine={false}
                axisLine={false}
                width={40}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload?.[0]) {
                    const d = payload[0].payload;
                    return (
                      <Paper sx={{ p: 1.5, border: '1px solid', borderColor: 'divider' }}>
                        <Typography variant="caption" sx={{ display: 'block' }}>
                          {d.range}: {d.count} spans
                        </Typography>
                      </Paper>
                    );
                  }
                  return null;
                }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {latencyHistogram.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={index < 2 ? '#22c55e' : index < 3 ? '#eab308' : index < 4 ? '#f97316' : '#ef4444'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </Paper>

      {/* Filters */}
      <FilterBar>
        <TextField
          placeholder="Trace ID, service, operation…"
          size="small"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <Search size={14} style={{ color: '#6b7280' }} />
                </InputAdornment>
              ),
            },
          }}
          sx={{ minWidth: 220, maxWidth: 300 }}
        />

        {/* Status code filter */}
        <ToggleButtonGroup value={statusFilter} exclusive onChange={(_, v) => v && setStatusFilter(v)} size="small">
          <ToggleButton value="all">All</ToggleButton>
          <ToggleButton value="2xx" sx={{ '&.Mui-selected': { color: '#22c55e' } }}>2xx</ToggleButton>
          <ToggleButton value="4xx" sx={{ '&.Mui-selected': { color: '#f97316' } }}>4xx</ToggleButton>
          <ToggleButton value="5xx" sx={{ '&.Mui-selected': { color: '#ef4444' } }}>5xx</ToggleButton>
        </ToggleButtonGroup>

        {/* Service filter */}
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel sx={{ fontSize: '0.8rem' }}>Service</InputLabel>
          <Select
            value={serviceFilter}
            label="Service"
            onChange={(e) => setServiceFilter(e.target.value)}
            sx={{ fontSize: '0.8rem' }}
          >
            {services.map((s) => (
              <MenuItem key={s} value={s} sx={{ fontSize: '0.8rem', fontFamily: s !== 'all' ? 'monospace' : 'inherit' }}>
                {s === 'all' ? 'All Services' : s}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Duration threshold */}
        <FormControl size="small" sx={{ minWidth: 130 }}>
          <InputLabel sx={{ fontSize: '0.8rem' }}>Min Duration</InputLabel>
          <Select
            value={durationFilter}
            label="Min Duration"
            onChange={(e) => setDurationFilter(e.target.value)}
            sx={{ fontSize: '0.8rem' }}
          >
            {DURATION_THRESHOLDS.map((o) => (
              <MenuItem key={o.value} value={o.value} sx={{ fontSize: '0.8rem' }}>{o.label}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <Typography variant="caption" sx={{ color: 'text.secondary', ml: 'auto' }}>
          {filtered.length} / {traces.length} spans
        </Typography>
      </FilterBar>

      {/* Table */}
      <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
        <TableContainer sx={{ maxHeight: 'calc(100dvh - 520px)' }}>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>Trace ID</TableCell>
                <TableCell>Service</TableCell>
                <TableCell>Operation</TableCell>
                <TableCell align="right">Duration</TableCell>
                <TableCell align="right">Status</TableCell>
                <TableCell>Time</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <LoadingRows cols={6} rows={8} />
              ) : filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6}>
                    <EmptyState message="No traces found" />
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((t, i) => (
                  <TableRow key={`${t.traceId}-${i}`} sx={{ '&:hover': { bgcolor: 'action.hover' } }}>
                    <TableCell sx={{ fontSize: '0.7rem', color: 'text.secondary', maxWidth: 110, overflow: 'hidden', textOverflow: 'ellipsis', fontFamily: 'monospace' }}>
                      {t.traceId}
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.75rem', color: 'primary.main', fontFamily: 'monospace' }}>
                      {t.serviceName}
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.75rem', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {t.operationName}
                    </TableCell>
                    <TableCell align="right" sx={{
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      fontVariantNumeric: 'tabular-nums',
                      color: durationColor(t.durationMs) || 'text.primary',
                    }}>
                      {t.durationMs}ms
                    </TableCell>
                    <TableCell align="right" sx={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      fontVariantNumeric: 'tabular-nums',
                      color: statusColor(t.statusCode),
                    }}>
                      {t.statusCode}
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.75rem', color: 'text.secondary', fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
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
