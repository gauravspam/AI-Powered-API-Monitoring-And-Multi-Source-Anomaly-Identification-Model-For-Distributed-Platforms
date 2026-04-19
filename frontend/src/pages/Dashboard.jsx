import { useMemo } from 'react';
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
  useTheme,
} from '@mui/material';
import {
  AreaChart, Area, BarChart, Bar, Cell,
  ComposedChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import {
  AlertTriangle, Server, Activity, Gauge, TrendingUp, CheckCircle,
  Clock, Zap, BarChart2,
} from 'lucide-react';
import { BACKEND_URL } from '@/api/http';
import {
  KpiCard, SeverityBadge, ScoreBar, timeAgo, EmptyState, LoadingRows, ChartTooltip,
} from '@/components/SharedComponents';
import { SEVERITY_COLORS } from '@/theme';

// ── proxyOrMock ───────────────────────────────────────────────────────────────
const proxyOrMock = async (path, mockFn) => {
  try {
    const r = await fetch(`${BACKEND_URL}${path}`, { signal: AbortSignal.timeout(5000) });
    if (!r.ok) throw new Error('Backend error');
    return r.json();
  } catch {
    const fallback = typeof mockFn === 'function' ? mockFn() : mockFn;
    return Array.isArray(fallback) ? [] : {};
  }
};

// ── Mock data ─────────────────────────────────────────────────────────────────
const generateMockOverview = () => ({
  totalServices: 12,
  totalMetrics: 15420,
  totalLogs: 8950,
  totalTraces: 4520,
  totalAnomalies: 23,
  activeAnomalies: 5,
  healthyServices: 10,
  degradedServices: 2,
  p99LatencyMs: 842,
  errorRatePct: 4.7,
  throughputRps: 18.4,
  errorBudgetBurnRate: 2.3,
  mttrMinutes: 14,
  _mock: true,
});

const generateMockAnomalies = () => {
  const services  = ['api-gateway', 'payment-service', 'user-service', 'auth-service', 'notification-service'];
  const endpoints = ['/api/users', '/payment/checkout', '/auth/login', '/api/orders', '/api/events'];
  const severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
  const statuses   = ['ACTIVE', 'ACKNOWLEDGED', 'RESOLVED'];
  return Array.from({ length: 20 }, (_, i) => ({
    id: 100 - i,
    apiName: services[i % services.length],
    endpoint: endpoints[i % endpoints.length],
    severity: severities[i % 4],
    hybridEnsembleScore: parseFloat((0.95 - i * 0.04).toFixed(3)),
    msifLstmScore: parseFloat((0.90 - i * 0.03).toFixed(3)),
    pleGruScore: parseFloat((0.93 - i * 0.04).toFixed(3)),
    status: statuses[i % 3],
    detectedAt: new Date(Date.now() - i * 900000).toISOString(),
    isAcknowledged: i % 3 === 1,
    isResolved: i % 3 === 2,
    _mock: true,
  }));
};

const normalizeAnomaly = (a, index) => ({
  id: a.id ?? index,
  apiName: a.apiName || a.api_name || a.serviceName || a.service_name || a.endpoint || 'unknown-service',
  endpoint: a.endpoint || a.apiName || a.api_name || 'n/a',
  severity: (a.severity || 'LOW').toUpperCase(),
  hybridEnsembleScore: a.hybridEnsembleScore ?? a.hybrid_ensemble_score ?? a.finalAnomalyScore ?? a.final_anomaly_score ?? 0,
  msifLstmScore: a.msifLstmScore ?? a.msif_lstm_score ?? 0,
  pleGruScore: a.pleGruScore ?? a.ple_gru_score ?? 0,
  status: (a.status || 'ACTIVE').toUpperCase(),
  detectedAt: a.detectedAt || a.timestamp || a.createdAt || a.created_at || null,
  isAcknowledged: a.isAcknowledged ?? (a.status || '').toUpperCase() === 'ACKNOWLEDGED',
  isResolved: a.isResolved ?? (a.status || '').toUpperCase() === 'RESOLVED',
});

const generateMockTraffic = () => {
  const now = Date.now();
  return Array.from({ length: 30 }, (_, i) => ({
    timestamp: new Date(now - (29 - i) * 60000).toISOString(),
    requestCount: 800 + Math.floor(Math.random() * 600),
    errorRate: parseFloat((0.01 + Math.random() * 0.08).toFixed(4)),
    avgLatencyMs: Math.floor(50 + Math.random() * 200),
    p99LatencyMs: Math.floor(200 + Math.random() * 800),
    p95LatencyMs: Math.floor(150 + Math.random() * 500),
  }));
};

// Spark trend helper
const genSpark = (base, variance, len = 12) =>
  Array.from({ length: len }, () => Math.max(0, base + (Math.random() - 0.5) * variance));

// ── Dashboard ─────────────────────────────────────────────────────────────────
export const Dashboard = () => {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const gridColor = isDark ? 'hsl(222, 14%, 16%)' : 'hsl(222, 14%, 88%)';
  const tickColor = isDark ? '#6b7280' : '#9ca3af';

  const { data: overview, isLoading: ovLoading } = useQuery({
    queryKey: ['/api/proxy/overview'],
    queryFn: () => proxyOrMock('/api/overview', generateMockOverview),
    refetchInterval: 30000,
  });

  const { data: anomalies, isLoading: anomLoading } = useQuery({
    queryKey: ['/api/proxy/anomalies'],
    queryFn: () => proxyOrMock('/api/anomalies/recent?limit=20', generateMockAnomalies),
    refetchInterval: 15000,
  });

  const { data: traffic, isLoading: trafficLoading } = useQuery({
    queryKey: ['/api/proxy/metrics/traffic'],
    queryFn: () => proxyOrMock('/api/metrics/traffic?limit=30', generateMockTraffic),
    refetchInterval: 30000,
  });

  const trafficData = useMemo(() =>
    (Array.isArray(traffic) ? traffic : []).map((t) => ({
      time: new Date(t.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      rps: parseFloat((t.requestCount / 60).toFixed(1)),
      errorRate: t.errorRate,
      p99: t.p99LatencyMs,
      p95: t.p95LatencyMs || Math.floor(t.p99LatencyMs * 0.75),
      avg: t.avgLatencyMs,
    })), [traffic]);

  const anomalyList = useMemo(() =>
    (Array.isArray(anomalies) ? anomalies : []).map((a, i) => normalizeAnomaly(a, i)).slice(0, 12), [anomalies]);

  const severityDistData = useMemo(() => {
    const counts = anomalyList.reduce((acc, a) => {
      acc[a.severity] = (acc[a.severity] || 0) + 1;
      return acc;
    }, {});
    return [
      { name: 'Critical', value: counts['CRITICAL'] || 0, fill: SEVERITY_COLORS.CRITICAL },
      { name: 'High',     value: counts['HIGH']     || 0, fill: SEVERITY_COLORS.HIGH },
      { name: 'Medium',   value: counts['MEDIUM']   || 0, fill: SEVERITY_COLORS.MEDIUM },
      { name: 'Low',      value: counts['LOW']      || 0, fill: SEVERITY_COLORS.LOW },
    ];
  }, [anomalyList]);

  // Sparkline data (mock trend direction)
  const latSpark  = genSpark(overview?.p99LatencyMs   || 842,  200);
  const errSpark  = genSpark(overview?.errorRatePct   || 4.7,  1.5);
const rpsSpark = genSpark(overview?.throughputRps || 18.4, 4);

  // KPI cards definition
  const kpis = [
    {
      label: 'P99 Latency',
      value: ovLoading ? '—' : `${overview?.p99LatencyMs ?? 842}ms`,
      sub: 'Tail latency across all services',
      accent: (overview?.p99LatencyMs ?? 0) > 1000 ? 'critical' : (overview?.p99LatencyMs ?? 0) > 500 ? 'high' : 'low',
      icon: Clock,
      delta: -3.2,
      deltaUnit: '%',
      lowerIsBetter: true,
      sparkData: latSpark,
      highlight: true,
    },
    {
      label: 'Error Rate',
      value: ovLoading ? '—' : `${(overview?.errorRatePct ?? 4.7).toFixed(1)}%`,
      sub: '4xx + 5xx combined',
      accent: (overview?.errorRatePct ?? 0) > 5 ? 'critical' : (overview?.errorRatePct ?? 0) > 2 ? 'high' : 'low',
      icon: AlertTriangle,
      delta: +0.4,
      deltaUnit: '%',
      lowerIsBetter: true,
      sparkData: errSpark,
      highlight: true,
    },
    {
      label: 'Throughput',
      value: ovLoading ? '—' : `${(overview?.throughputRps ?? 18.4).toFixed(1)} RPS`,
      sub: 'Request rate (all services)',
      accent: 'default',
      icon: Zap,
      delta: +2.1,
      deltaUnit: '%',
      sparkData: rpsSpark,
    },
    {
      label: 'Active Anomalies',
      value: ovLoading ? '—' : overview?.activeAnomalies ?? 5,
      sub: 'Require immediate attention',
      accent: (overview?.activeAnomalies ?? 0) > 3 ? 'critical' : (overview?.activeAnomalies ?? 0) > 0 ? 'high' : 'low',
      icon: AlertTriangle,
      highlight: (overview?.activeAnomalies ?? 0) > 0,
    },
    {
      label: 'MTTR',
      value: ovLoading ? '—' : `${overview?.mttrMinutes ?? 14}m`,
      sub: 'Mean time to resolve',
      accent: (overview?.mttrMinutes ?? 0) > 30 ? 'high' : 'low',
      icon: Clock,
    },
    {
      label: 'Healthy Services',
      value: ovLoading ? '—' : `${overview?.healthyServices ?? 10} / ${overview?.totalServices ?? 12}`,
      sub: `${overview?.degradedServices ?? 2} degraded`,
      accent: (overview?.degradedServices ?? 0) > 0 ? 'high' : 'low',
      icon: Server,
    },
    {
      label: 'Total Anomalies',
      value: ovLoading ? '—' : overview?.totalAnomalies ?? 23,
      sub: 'All time detected',
      accent: 'info',
      icon: Activity,
    },
  ];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
      {/* ── Golden Signals KPI row ── */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 1.5 }}>
        {kpis.map((kpi) => (
          <KpiCard key={kpi.label} {...kpi} />
        ))}
      </Box>

      {/* ── Charts row ── */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
        {/* Traffic + Error Rate combo chart */}
        <Box sx={{ flex: '1 1 500px', minWidth: 300 }}>
          <Paper elevation={0} sx={{ p: 2, border: '1px solid', borderColor: 'divider' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                Traffic & Error Rate
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>Last 30 min</Typography>
            </Box>
            {trafficLoading ? (
              <Box sx={{ height: 180, bgcolor: 'action.hover', borderRadius: 1 }} />
            ) : trafficData.length === 0 ? (
              <EmptyState message="No traffic data" />
            ) : (
              <ResponsiveContainer width="100%" height={180}>
                <ComposedChart data={trafficData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                  <defs>
                    <linearGradient id="gradRps" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="hsl(188, 80%, 42%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(188, 80%, 42%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
                  <XAxis dataKey="time" tick={{ fontSize: 10, fill: tickColor }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                  <YAxis yAxisId="rps" tick={{ fontSize: 10, fill: tickColor }} tickLine={false} axisLine={false} width={36} />
                  <YAxis yAxisId="err" orientation="right" tick={{ fontSize: 10, fill: tickColor }} tickLine={false} axisLine={false} width={40}
                    tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                  <Tooltip content={<ChartTooltip />} />
                  <Legend iconType="circle" iconSize={7} wrapperStyle={{ fontSize: '0.7rem' }} />
                  <Area yAxisId="rps" type="monotone" dataKey="rps" name="RPS" stroke="hsl(188, 80%, 42%)" fill="url(#gradRps)" strokeWidth={1.5} dot={false} />
                  <Line yAxisId="err" type="monotone" dataKey="errorRate" name="Error Rate" stroke="#ef4444" strokeWidth={1.5} dot={false} />
                </ComposedChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Box>

        {/* Severity distribution */}
        <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
          <Paper elevation={0} sx={{ p: 2, border: '1px solid', borderColor: 'divider' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>Anomaly Severity</Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>Recent {anomalyList.length}</Typography>
            </Box>
            {anomLoading ? (
              <Box sx={{ height: 180, bgcolor: 'action.hover', borderRadius: 1 }} />
            ) : (
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={severityDistData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: tickColor }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: tickColor }} tickLine={false} axisLine={false} allowDecimals={false} width={24} />
                  <Tooltip content={<ChartTooltip />} />
                  <Bar dataKey="value" name="Count" radius={[3, 3, 0, 0]}>
                    {severityDistData.map((entry, idx) => (
                      <Cell key={idx} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Box>
      </Box>

      {/* ── P99 / P95 / Avg Latency chart ── */}
      <Paper elevation={0} sx={{ p: 2, border: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>Latency Percentiles</Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>Last 30 min · P99 / P95 / Avg</Typography>
        </Box>
        {trafficLoading ? (
          <Box sx={{ height: 120, bgcolor: 'action.hover', borderRadius: 1 }} />
        ) : trafficData.length === 0 ? (
          <EmptyState message="No data" />
        ) : (
          <ResponsiveContainer width="100%" height={120}>
            <AreaChart data={trafficData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
              <defs>
                <linearGradient id="gradP99" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#f97316" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: tickColor }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 10, fill: tickColor }} tickLine={false} axisLine={false} width={42} unit="ms" />
              <Tooltip content={<ChartTooltip />} />
              <Legend iconType="circle" iconSize={7} wrapperStyle={{ fontSize: '0.7rem' }} />
              <Area type="monotone" dataKey="p99" name="P99" stroke="#f97316" fill="url(#gradP99)" strokeWidth={1.5} dot={false} />
              <Area type="monotone" dataKey="p95" name="P95" stroke="#eab308" fill="transparent" strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
              <Area type="monotone" dataKey="avg" name="Avg" stroke="hsl(188, 80%, 42%)" fill="transparent" strokeWidth={1} dot={false} strokeDasharray="2 3" />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </Paper>

      {/* ── Recent Anomalies table ── */}
      <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
        <Box sx={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          p: 2, borderBottom: '1px solid', borderColor: 'divider',
        }}>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>Recent Anomalies</Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            {anomalyList.length} most recent
          </Typography>
        </Box>
        <TableContainer sx={{ maxHeight: 380 }}>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                {['Service', 'Endpoint', 'Severity', 'Hybrid Score', 'Status', 'Detected'].map((col) => (
                  <TableCell key={col}>{col}</TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {anomLoading ? (
                <LoadingRows cols={6} rows={7} />
              ) : anomalyList.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6}><EmptyState message="No anomalies detected" icon="✓" /></TableCell>
                </TableRow>
              ) : (
                anomalyList.map((a, i) => (
                  <TableRow key={a.id ?? i} sx={{ '&:hover': { bgcolor: 'action.hover' } }}>
                    <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'primary.main', fontWeight: 500 }}>
                      {a.apiName}
                    </TableCell>
                    <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'text.secondary', maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {a.endpoint}
                    </TableCell>
                    <TableCell><SeverityBadge severity={a.severity} /></TableCell>
                    <TableCell sx={{ minWidth: 160 }}>
                      <ScoreBar score={a.hybridEnsembleScore || a.hybridScore || 0} />
                    </TableCell>
                    <TableCell><SeverityBadge severity={a.status} /></TableCell>
                    <TableCell sx={{ fontSize: '0.75rem', color: 'text.secondary', whiteSpace: 'nowrap' }}>
                      {timeAgo(a.detectedAt)}
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

export default Dashboard;
