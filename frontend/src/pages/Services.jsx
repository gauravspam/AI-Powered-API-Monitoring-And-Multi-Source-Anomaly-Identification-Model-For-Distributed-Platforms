import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box, Paper, Typography, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, TextField, ToggleButtonGroup, ToggleButton,
  InputAdornment, MenuItem, Select, FormControl, InputLabel, Chip,
} from '@mui/material';
import { Search, Server, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import { BACKEND_URL } from '@/api/http';
import { StatusDot, EmptyState, LoadingRows, KpiCard, FilterBar } from '@/components/SharedComponents';

const proxyOrMock = async (path, mockFn) => {
  try {
    const r = await fetch(`${BACKEND_URL}${path}`, { signal: AbortSignal.timeout(5000) });
    if (!r.ok) throw new Error();
    return r.json();
  } catch {
    return mockFn();
  }
};

const generateMockServices = () => [
  { id: 1, name: 'api-gateway',         ownerTeam: 'Platform',  status: 'healthy',  p99LatencyMs: 98,  avgLatencyMs: 45,  errorRate: 0.02,  anomalyRate: 0.10, requestPerMin: 1200, p99Trend: [78,82,91,95,90,98] },
  { id: 2, name: 'payment-service',      ownerTeam: 'Commerce',  status: 'degraded', p99LatencyMs: 1240,avgLatencyMs: 312, errorRate: 0.08,  anomalyRate: 0.40, requestPerMin: 340,  p99Trend: [320,450,680,900,1100,1240] },
  { id: 3, name: 'user-service',         ownerTeam: 'Identity',  status: 'healthy',  p99LatencyMs: 145, avgLatencyMs: 67,  errorRate: 0.01,  anomalyRate: 0.05, requestPerMin: 890,  p99Trend: [130,135,140,138,142,145] },
  { id: 4, name: 'auth-service',         ownerTeam: 'Identity',  status: 'healthy',  p99LatencyMs: 72,  avgLatencyMs: 38,  errorRate: 0.005, anomalyRate: 0.02, requestPerMin: 2100, p99Trend: [68,70,71,69,73,72] },
  { id: 5, name: 'notification-service', ownerTeam: 'Comms',     status: 'healthy',  p99LatencyMs: 220, avgLatencyMs: 95,  errorRate: 0.03,  anomalyRate: 0.15, requestPerMin: 450,  p99Trend: [210,215,218,220,222,220] },
  { id: 6, name: 'inventory-service',    ownerTeam: 'Commerce',  status: 'healthy',  p99LatencyMs: 280, avgLatencyMs: 112, errorRate: 0.02,  anomalyRate: 0.08, requestPerMin: 220,  p99Trend: [260,265,270,275,278,280] },
  { id: 7, name: 'analytics-service',    ownerTeam: 'Data',      status: 'degraded', p99LatencyMs: 2100,avgLatencyMs: 890, errorRate: 0.12,  anomalyRate: 0.55, requestPerMin: 180,  p99Trend: [700,900,1200,1600,1900,2100] },
  { id: 8, name: 'search-service',       ownerTeam: 'Discovery', status: 'healthy',  p99LatencyMs: 180, avgLatencyMs: 78,  errorRate: 0.01,  anomalyRate: 0.06, requestPerMin: 760,  p99Trend: [168,172,175,178,180,180] },
  { id: 9, name: 'order-service',        ownerTeam: 'Commerce',  status: 'down',     p99LatencyMs: null,avgLatencyMs: null,errorRate: 1.0,   anomalyRate: 1.0,  requestPerMin: 0,    p99Trend: [340,280,180,80,0,0] },
  { id: 10,name: 'email-service',        ownerTeam: 'Comms',     status: 'healthy',  p99LatencyMs: 310, avgLatencyMs: 140, errorRate: 0.015, anomalyRate: 0.04, requestPerMin: 320,  p99Trend: [295,300,305,308,310,310] },
];

const ANOMALY_RATE_OPTIONS = [
  { label: 'All Rates', value: 'all' },
  { label: '>10%',      value: 0.10 },
  { label: '>25%',      value: 0.25 },
  { label: '>50%',      value: 0.50 },
];

const latencyColor = (ms) => {
  if (!ms) return '#6b7280';
  if (ms > 1000) return '#ef4444';
  if (ms > 500)  return '#f97316';
  if (ms > 200)  return '#eab308';
  return undefined; // default text color
};

const errorColor = (rate) => {
  if (rate >= 1.0) return '#ef4444';
  if (rate > 0.1)  return '#ef4444';
  if (rate > 0.05) return '#f97316';
  return undefined;
};

const anomalyColor = (rate) => {
  if (rate > 0.5)  return '#ef4444';
  if (rate > 0.25) return '#f97316';
  if (rate > 0.1)  return '#eab308';
  return undefined;
};

export const Services = () => {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [teamFilter, setTeamFilter] = useState('all');
  const [anomalyRateFilter, setAnomalyRateFilter] = useState('all');

  const { data: services, isLoading } = useQuery({
    queryKey: ['/api/proxy/services'],
    queryFn: () => proxyOrMock('/api/services', generateMockServices),
    refetchInterval: 30000,
  });

  const serviceList = Array.isArray(services) ? services : [];

  const teams = useMemo(() => {
    const t = [...new Set(serviceList.map((s) => s.ownerTeam).filter(Boolean))].sort();
    return ['all', ...t];
  }, [serviceList]);

  const filtered = useMemo(() =>
    serviceList.filter((s) => {
      const matchSearch = !search ||
        s.name.toLowerCase().includes(search.toLowerCase()) ||
        s.ownerTeam?.toLowerCase().includes(search.toLowerCase());
      const matchStatus = statusFilter === 'all' || s.status === statusFilter;
      const matchTeam   = teamFilter   === 'all' || s.ownerTeam === teamFilter;
      const matchAnomaly = anomalyRateFilter === 'all' || s.anomalyRate >= anomalyRateFilter;
      return matchSearch && matchStatus && matchTeam && matchAnomaly;
    }), [serviceList, search, statusFilter, teamFilter, anomalyRateFilter]);

  const healthy  = serviceList.filter((s) => s.status === 'healthy').length;
  const degraded = serviceList.filter((s) => s.status === 'degraded').length;
  const down     = serviceList.filter((s) => s.status === 'down').length;

  const highAnomalyCount = serviceList.filter((s) => s.anomalyRate > 0.25).length;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
      {/* Summary KPIs */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 1.5 }}>
        <KpiCard label="Total Services"   value={serviceList.length} sub="Monitored"        accent="default" icon={Server} />
        <KpiCard label="Healthy"          value={healthy}            sub="Nominal operation" accent="low"     icon={CheckCircle} />
        <KpiCard label="Degraded"         value={degraded}           sub="High latency / errors" accent={degraded > 0 ? 'high' : 'low'} icon={AlertTriangle} highlight={degraded > 0} />
        <KpiCard label="Down"             value={down}               sub="No response"       accent={down > 0 ? 'critical' : 'low'} icon={XCircle} highlight={down > 0} />
        <KpiCard label="High Anomaly Rate" value={highAnomalyCount} sub=">25% anomaly rate" accent={highAnomalyCount > 0 ? 'high' : 'low'} icon={AlertTriangle} highlight={highAnomalyCount > 0} />
      </Box>

      {/* Filters */}
      <FilterBar>
        <TextField
          placeholder="Search service or team…"
          size="small"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <Search size={15} style={{ color: '#6b7280' }} />
                </InputAdornment>
              ),
            },
          }}
          sx={{ minWidth: 220, maxWidth: 280 }}
        />

        {/* Status filter */}
        <ToggleButtonGroup
          value={statusFilter}
          exclusive
          onChange={(_, v) => v && setStatusFilter(v)}
          size="small"
        >
          <ToggleButton value="all">All</ToggleButton>
          <ToggleButton value="healthy"
            sx={{ '&.Mui-selected': { color: '#22c55e', borderColor: '#22c55e50' } }}
          >Healthy</ToggleButton>
          <ToggleButton value="degraded"
            sx={{ '&.Mui-selected': { color: '#f97316', borderColor: '#f9731650' } }}
          >Degraded</ToggleButton>
          <ToggleButton value="down"
            sx={{ '&.Mui-selected': { color: '#ef4444', borderColor: '#ef444450' } }}
          >Down</ToggleButton>
        </ToggleButtonGroup>

        {/* Team filter */}
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel sx={{ fontSize: '0.8rem' }}>Team</InputLabel>
          <Select
            value={teamFilter}
            label="Team"
            onChange={(e) => setTeamFilter(e.target.value)}
            sx={{ fontSize: '0.8rem' }}
          >
            {teams.map((t) => (
              <MenuItem key={t} value={t} sx={{ fontSize: '0.8rem' }}>
                {t === 'all' ? 'All Teams' : t}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Anomaly rate threshold */}
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel sx={{ fontSize: '0.8rem' }}>Anomaly Rate</InputLabel>
          <Select
            value={anomalyRateFilter}
            label="Anomaly Rate"
            onChange={(e) => setAnomalyRateFilter(e.target.value)}
            sx={{ fontSize: '0.8rem' }}
          >
            {ANOMALY_RATE_OPTIONS.map((o) => (
              <MenuItem key={o.value} value={o.value} sx={{ fontSize: '0.8rem' }}>
                {o.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Typography variant="caption" sx={{ color: 'text.secondary', ml: 'auto' }}>
          {filtered.length} / {serviceList.length} services
        </Typography>
      </FilterBar>

      {/* Table */}
      <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
        <TableContainer sx={{ maxHeight: 'calc(100dvh - 380px)' }}>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                {[
                  { label: 'Service',      align: 'left'  },
                  { label: 'Team',         align: 'left'  },
                  { label: 'Status',       align: 'left'  },
                  { label: 'P99 Latency',  align: 'right' },
                  { label: 'Avg Latency',  align: 'right' },
                  { label: 'Error Rate',   align: 'right' },
                  { label: 'Anomaly Rate', align: 'right' },
                  { label: 'Req/min',      align: 'right' },
                ].map(({ label, align }) => (
                  <TableCell key={label} align={align}>{label}</TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <LoadingRows cols={8} rows={6} />
              ) : filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8}>
                    <EmptyState message="No services match filters" />
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((s) => (
                  <TableRow key={s.id} sx={{ '&:hover': { bgcolor: 'action.hover' } }}>
                    <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'primary.main', fontWeight: 500 }}>
                      {s.name}
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>
                      {s.ownerTeam}
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                        <StatusDot status={s.status} />
                        <Typography variant="caption" sx={{ textTransform: 'capitalize', fontWeight: 500 }}>
                          {s.status}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right" sx={{
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      fontVariantNumeric: 'tabular-nums',
                      color: latencyColor(s.p99LatencyMs) || 'text.primary',
                    }}>
                      {s.p99LatencyMs ? `${s.p99LatencyMs}ms` : '—'}
                    </TableCell>
                    <TableCell align="right" sx={{
                      fontSize: '0.75rem',
                      fontVariantNumeric: 'tabular-nums',
                      color: latencyColor(s.avgLatencyMs) || 'text.secondary',
                    }}>
                      {s.avgLatencyMs ? `${s.avgLatencyMs}ms` : '—'}
                    </TableCell>
                    <TableCell align="right" sx={{
                      fontSize: '0.75rem',
                      fontWeight: 500,
                      fontVariantNumeric: 'tabular-nums',
                      color: errorColor(s.errorRate) || 'text.primary',
                    }}>
                      {(s.errorRate * 100).toFixed(1)}%
                    </TableCell>
                    <TableCell align="right" sx={{
                      fontSize: '0.75rem',
                      fontWeight: 500,
                      fontVariantNumeric: 'tabular-nums',
                      color: anomalyColor(s.anomalyRate) || 'text.primary',
                    }}>
                      {(s.anomalyRate * 100).toFixed(0)}%
                    </TableCell>
                    <TableCell align="right" sx={{
                      fontSize: '0.75rem',
                      fontVariantNumeric: 'tabular-nums',
                      color: s.requestPerMin === 0 ? 'error.main' : 'text.primary',
                    }}>
                      {s.requestPerMin?.toLocaleString() ?? '—'}
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

export default Services;
