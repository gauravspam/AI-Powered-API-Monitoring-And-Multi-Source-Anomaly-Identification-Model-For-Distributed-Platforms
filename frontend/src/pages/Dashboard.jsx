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
} from '@mui/material';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import {
  Warning as WarningIcon,
  Speed as SpeedIcon,
  Dns as DnsIcon,
  Description as DescriptionIcon,
  AccountTree as AccountTreeIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { BACKEND_URL } from '@/api/http';
import { KpiCard, SeverityBadge, ScoreBar, timeAgo, EmptyState } from '@/components/SharedComponents';

// ── Helper: try backend, fall back to mock ──────────────────────────────────
const proxyOrMock = async (path, mockFn) => {
  try {
    const resp = await fetch(`${BACKEND_URL}${path}`, { signal: AbortSignal.timeout(5000) });
    if (!resp.ok) throw new Error('Backend error');
    return await resp.json();
  } catch {
    return mockFn();
  }
};

// ── Mock generators ──────────────────────────────────────────────────────────
const generateMockOverview = () => ({
  totalServices: 12,
  totalMetrics: 15420,
  totalLogs: 8950,
  totalTraces: 4520,
  totalAnomalies: 23,
  activeAnomalies: 5,
  healthyServices: 10,
  degradedServices: 2,
  _mock: true,
});

const generateMockAnomalies = () => {
  const services = ['api-gateway', 'payment-service', 'user-service', 'auth-service', 'notification-service'];
  const endpoints = ['/api/users', '/payment/checkout', '/auth/login', '/api/orders', '/api/events'];
  const severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
  const statuses = ['ACTIVE', 'ACKNOWLEDGED', 'RESOLVED'];
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
    environment: i % 2 === 0 ? 'production' : 'staging',
    _mock: true,
  }));
};

const generateMockTrafficMetrics = () => {
  const now = Date.now();
  return Array.from({ length: 30 }, (_, i) => ({
    timestamp: new Date(now - (29 - i) * 60000).toISOString(),
    requestCount: 800 + Math.floor(Math.random() * 600),
    errorRate: parseFloat((0.01 + Math.random() * 0.08).toFixed(4)),
    avgLatencyMs: Math.floor(50 + Math.random() * 200),
    p99LatencyMs: Math.floor(200 + Math.random() * 800),
  }));
};

// ── Custom tooltip for Recharts ──────────────────────────────────────────────
const CustomTooltip = ({ active, payload, label }) => {
  if (active && Array.isArray(payload) && payload.length) {
    return (
      <Paper sx={{ p: 1.5, border: '1px solid', borderColor: 'divider' }}>
        <Typography variant="caption" sx={{ color: 'text.secondary', mb: 0.5, display: 'block' }}>
          {label}
        </Typography>
        {payload.map((p) => (
          <Typography
            key={p.dataKey}
            variant="caption"
            sx={{ display: 'block', color: p.color, fontVariantNumeric: 'tabular-nums' }}
          >
            {p.dataKey}:{' '}
            {typeof p.value === 'number'
              ? p.dataKey?.includes('Rate')
                ? (p.value * 100).toFixed(2) + '%'
                : p.value.toLocaleString()
              : p.value}
          </Typography>
        ))}
      </Paper>
    );
  }
  return null;
};

// ── Page component ───────────────────────────────────────────────────────────
export const Dashboard = () => {
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
    queryFn: () => proxyOrMock('/api/metrics/traffic?limit=30', generateMockTrafficMetrics),
    refetchInterval: 30000,
  });

  const trafficData = Array.isArray(traffic)
    ? traffic.map((t) => ({
        time: new Date(t.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        requests: t.requestCount,
        errorRate: t.errorRate,
        latency: t.avgLatencyMs,
      }))
    : [];

  const anomalyList = Array.isArray(anomalies) ? anomalies.slice(0, 10) : [];

  const severityCounts = anomalyList.reduce((acc, a) => {
    const s = a.severity || 'NORMAL';
    acc[s] = (acc[s] || 0) + 1;
    return acc;
  }, {});

  const severityDistData = [
    { name: 'Critical', value: severityCounts['CRITICAL'] || 0, fill: '#ef4444' },
    { name: 'High',     value: severityCounts['HIGH']     || 0, fill: '#f97316' },
    { name: 'Medium',   value: severityCounts['MEDIUM']   || 0, fill: '#eab308' },
    { name: 'Low',      value: severityCounts['LOW']      || 0, fill: '#22c55e' },
  ];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* KPI row */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
        {[
          {
            label: 'Active Anomalies',
            value: ovLoading ? '—' : overview?.activeAnomalies ?? 0,
            sub: 'Require attention',
            accent: 'critical',
            icon: <WarningIcon sx={{ fontSize: 14 }} />,
          },
          {
            label: 'Total Services',
            value: ovLoading ? '—' : overview?.totalServices ?? 0,
            sub: `${overview?.degradedServices ?? 0} degraded`,
            accent: overview?.degradedServices > 0 ? 'high' : 'low',
            icon: <DnsIcon sx={{ fontSize: 14 }} />,
          },
          {
            label: 'Metrics Ingested',
            value: ovLoading ? '—' : (overview?.totalMetrics ?? 0).toLocaleString(),
            sub: 'All time',
            icon: <SpeedIcon sx={{ fontSize: 14 }} />,
          },
          {
            label: 'Log Entries',
            value: ovLoading ? '—' : (overview?.totalLogs ?? 0).toLocaleString(),
            sub: 'OpenSearch indexed',
            icon: <DescriptionIcon sx={{ fontSize: 14 }} />,
          },
          {
            label: 'Trace Spans',
            value: ovLoading ? '—' : (overview?.totalTraces ?? 0).toLocaleString(),
            sub: 'Distributed traces',
            icon: <AccountTreeIcon sx={{ fontSize: 14 }} />,
          },
          {
            label: 'Total Anomalies',
            value: ovLoading ? '—' : overview?.totalAnomalies ?? 0,
            sub: 'All time detected',
            accent: 'info',
            icon: <TrendingUpIcon sx={{ fontSize: 14 }} />,
          },
        ].map((kpi) => (
          <Box key={kpi.label} sx={{ flex: '1 1 140px', minWidth: 140 }}>
            <KpiCard {...kpi} />
          </Box>
        ))}
      </Box>

      {/* Charts row */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
        {/* Traffic area chart */}
        <Box sx={{ flex: '1 1 500px', minWidth: 300 }}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.secondary' }}>
                Request Traffic
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                Last 30 min
              </Typography>
            </Box>
            {trafficLoading ? (
              <Box sx={{ height: 176, bgcolor: 'action.hover', borderRadius: 1 }} />
            ) : trafficData.length === 0 ? (
              <EmptyState message="No traffic data" />
            ) : (
              <ResponsiveContainer width="100%" height={176}>
                <AreaChart data={trafficData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                  <defs>
                    <linearGradient id="gradRequests" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(188, 80%, 42%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(188, 80%, 42%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e2a38" vertical={false} />
                  <XAxis
                    dataKey="time"
                    tick={{ fontSize: 10, fill: '#6b7280' }}
                    tickLine={false}
                    axisLine={false}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: '#6b7280' }}
                    tickLine={false}
                    axisLine={false}
                    width={40}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="requests"
                    name="Requests"
                    stroke="hsl(188, 80%, 42%)"
                    fill="url(#gradRequests)"
                    strokeWidth={1.5}
                    dot={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Box>

        {/* Severity bar chart */}
        <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.secondary' }}>
                Severity Distribution
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                Recent 10
              </Typography>
            </Box>
            {anomLoading ? (
              <Box sx={{ height: 176, bgcolor: 'action.hover', borderRadius: 1 }} />
            ) : (
              <ResponsiveContainer width="100%" height={176}>
                <BarChart data={severityDistData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e2a38" vertical={false} />
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 10, fill: '#6b7280' }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: '#6b7280' }}
                    tickLine={false}
                    axisLine={false}
                    allowDecimals={false}
                    width={25}
                  />
                  <Tooltip content={<CustomTooltip />} />
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

      {/* Error rate & latency chart */}
      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.secondary' }}>
            Error Rate & Latency
          </Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            Last 30 min
          </Typography>
        </Box>
        {trafficLoading ? (
          <Box sx={{ height: 128, bgcolor: 'action.hover', borderRadius: 1 }} />
        ) : trafficData.length === 0 ? (
          <EmptyState message="No data" />
        ) : (
          <ResponsiveContainer width="100%" height={128}>
            <AreaChart data={trafficData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2a38" vertical={false} />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 10, fill: '#6b7280' }}
                tickLine={false}
                axisLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 10, fill: '#6b7280' }}
                tickLine={false}
                axisLine={false}
                width={40}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
              <Area
                type="monotone"
                dataKey="errorRate"
                name="Error Rate"
                stroke="#ef4444"
                fill="transparent"
                strokeWidth={1.5}
                dot={false}
              />
              <Area
                type="monotone"
                dataKey="latency"
                name="Latency (ms)"
                stroke="#f97316"
                fill="transparent"
                strokeWidth={1.5}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </Paper>

      {/* Recent anomalies table */}
      <Paper>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            p: 2,
            borderBottom: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            Recent Anomalies
          </Typography>
        </Box>
        <TableContainer sx={{ maxHeight: 400 }}>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                {['Service', 'Endpoint', 'Severity', 'Hybrid Score', 'Status', 'Detected'].map(
                  (col) => (
                    <TableCell key={col} sx={{ fontWeight: 600, fontSize: '0.7rem', color: 'text.secondary' }}>
                      {col}
                    </TableCell>
                  )
                )}
              </TableRow>
            </TableHead>
            <TableBody>
              {anomLoading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 6 }).map((__, j) => (
                      <TableCell key={j}>
                        <Box sx={{ height: 12, bgcolor: 'action.hover', borderRadius: 1, width: '60%' }} />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : anomalyList.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6}>
                    <EmptyState message="No anomalies detected" />
                  </TableCell>
                </TableRow>
              ) : (
                anomalyList.map((a, i) => (
                  <TableRow key={i} sx={{ '&:hover': { bgcolor: 'action.hover' } }}>
                    <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'primary.main' }}>
                      {a.apiName}
                    </TableCell>
                    <TableCell
                      sx={{
                        fontFamily: 'monospace',
                        fontSize: '0.75rem',
                        color: 'text.secondary',
                        maxWidth: 160,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {a.endpoint}
                    </TableCell>
                    <TableCell>
                      <SeverityBadge severity={a.severity} />
                    </TableCell>
                    <TableCell>
                      <ScoreBar score={a.hybridEnsembleScore || a.hybridScore || 0} />
                    </TableCell>
                    <TableCell>
                      <SeverityBadge severity={a.status} />
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>
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
