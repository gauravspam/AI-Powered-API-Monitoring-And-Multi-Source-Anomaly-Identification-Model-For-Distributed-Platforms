import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box, Paper, Typography, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, ToggleButtonGroup, ToggleButton, IconButton,
  Snackbar, Alert, TextField, InputAdornment, MenuItem, Select, FormControl,
  InputLabel, Tooltip,
} from '@mui/material';
import { CheckCircle, XCircle, RefreshCcw, Search, Clock } from 'lucide-react';
import { BACKEND_URL } from '@/api/http';
import {
  SeverityBadge, ScoreBar, timeAgo, EmptyState, LoadingRows, KpiCard, FilterBar,
} from '@/components/SharedComponents';

const proxyOrMock = async (path, mockFn) => {
  try {
    const r = await fetch(`${BACKEND_URL}${path}`, { signal: AbortSignal.timeout(5000) });
    if (!r.ok) throw new Error();
    return r.json();
  } catch {
    return mockFn();
  }
};

const generateMockAlerts = () => {
  const services  = ['api-gateway', 'payment-service', 'user-service', 'auth-service', 'notification-service'];
  const endpoints = ['/api/users', '/payment/checkout', '/auth/login', '/api/orders', '/api/events'];
  const severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
  const statuses   = ['ACTIVE', 'ACKNOWLEDGED', 'RESOLVED'];
  return Array.from({ length: 25 }, (_, i) => ({
    id: 100 - i,
    apiName: services[i % services.length],
    endpoint: endpoints[i % endpoints.length],
    severity: severities[i % 4],
    hybridEnsembleScore: parseFloat((0.95 - i * 0.04).toFixed(3)),
    msifLstmScore: parseFloat((0.90 - i * 0.03).toFixed(3)),
    pleGruScore: parseFloat((0.93 - i * 0.04).toFixed(3)),
    status: statuses[i % 3],
    detectedAt: new Date(Date.now() - i * 900000).toISOString(),
    acknowledgedAt: i % 3 === 1 ? new Date(Date.now() - i * 800000).toISOString() : null,
    resolvedAt: i % 3 === 2 ? new Date(Date.now() - i * 600000).toISOString() : null,
    isAcknowledged: i % 3 === 1,
    isResolved: i % 3 === 2,
    _mock: true,
  }));
};

const normalizeAlert = (a, index) => {
  const detectedAt = a.detectedAt || a.timestamp || a.createdAt || a.created_at || null;
  const resolvedAt = a.resolvedAt || a.resolved_at || null;
  const status = (a.status || 'ACTIVE').toUpperCase();

  return {
    id: a.id ?? index,
    apiName: a.apiName || a.api_name || a.serviceName || a.service_name || a.endpoint || 'unknown-service',
    endpoint: a.endpoint || a.apiName || a.api_name || 'n/a',
    severity: (a.severity || 'LOW').toUpperCase(),
    hybridEnsembleScore: a.hybridEnsembleScore ?? a.hybrid_ensemble_score ?? a.finalAnomalyScore ?? a.final_anomaly_score ?? 0,
    msifLstmScore: a.msifLstmScore ?? a.msif_lstm_score ?? 0,
    pleGruScore: a.pleGruScore ?? a.ple_gru_score ?? 0,
    status,
    detectedAt,
    resolvedAt,
    isAcknowledged: a.isAcknowledged ?? status === 'ACKNOWLEDGED',
    isResolved: a.isResolved ?? status === 'RESOLVED',
  };
};

// Compute MTTR for resolved anomalies (detected → resolved)
const calcMttr = (anomaly) => {
  if (!anomaly.resolvedAt || !anomaly.detectedAt) return null;
  return Math.round((new Date(anomaly.resolvedAt) - new Date(anomaly.detectedAt)) / 60000);
};

const TIME_RANGE_OPTIONS = [
  { label: 'Last 1h',  value: 1  },
  { label: 'Last 6h',  value: 6  },
  { label: 'Last 24h', value: 24 },
  { label: 'Last 7d',  value: 168 },
  { label: 'All time', value: 0  },
];

export const Alerts = () => {
  const queryClient = useQueryClient();
  const [severityFilter,  setSeverityFilter]  = useState('all');
  const [statusFilter,    setStatusFilter]     = useState('all');
  const [serviceSearch,   setServiceSearch]    = useState('');
  const [timeRange,       setTimeRange]        = useState(0);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  const { data: anomalies, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['/api/proxy/alerts'],
    queryFn: () => proxyOrMock('/api/anomalies?limit=30', generateMockAlerts),
    refetchInterval: 15000,
  });

  // Acknowledge
  const acknowledge = useMutation({
    mutationFn: async (id) => {
      const res = await fetch(`${BACKEND_URL}/api/anomalies/${id}/acknowledge`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed');
      return res.json();
    },
    onSuccess: () => {
      setSnackbar({ open: true, message: 'Anomaly acknowledged', severity: 'success' });
      queryClient.invalidateQueries({ queryKey: ['/api/proxy/alerts'] });
      queryClient.invalidateQueries({ queryKey: ['/api/sidebar/badge'] });
    },
    onError: () => setSnackbar({ open: true, message: 'Action failed — backend offline', severity: 'error' }),
  });

  // Resolve
  const resolve = useMutation({
    mutationFn: async (id) => {
      const res = await fetch(`${BACKEND_URL}/api/anomalies/${id}/resolve`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed');
      return res.json();
    },
    onSuccess: () => {
      setSnackbar({ open: true, message: 'Anomaly resolved', severity: 'success' });
      queryClient.invalidateQueries({ queryKey: ['/api/proxy/alerts'] });
      queryClient.invalidateQueries({ queryKey: ['/api/sidebar/badge'] });
    },
    onError: () => setSnackbar({ open: true, message: 'Action failed — backend offline', severity: 'error' }),
  });

  const allAlerts = useMemo(
    () => (Array.isArray(anomalies) ? anomalies.map((a, i) => normalizeAlert(a, i)) : []),
    [anomalies]
  );

  const filtered = useMemo(() => {
    const now = Date.now();
    const cutoff = timeRange > 0 ? now - timeRange * 60 * 60 * 1000 : 0;
    return allAlerts.filter((a) => {
      const matchSev     = severityFilter  === 'all' || a.severity === severityFilter;
      const matchStat    = statusFilter    === 'all' || a.status   === statusFilter;
      const matchService = !serviceSearch  ||
        a.apiName?.toLowerCase().includes(serviceSearch.toLowerCase()) ||
        a.endpoint?.toLowerCase().includes(serviceSearch.toLowerCase());
      const detectedMs = a.detectedAt ? new Date(a.detectedAt).getTime() : null;
      const matchTime = timeRange === 0 || (detectedMs !== null && !Number.isNaN(detectedMs) && detectedMs >= cutoff);
      return matchSev && matchStat && matchService && matchTime;
    });
  }, [allAlerts, severityFilter, statusFilter, serviceSearch, timeRange]);

  const counts = useMemo(() => ({
    CRITICAL:     allAlerts.filter((a) => a.severity === 'CRITICAL').length,
    HIGH:         allAlerts.filter((a) => a.severity === 'HIGH').length,
    ACTIVE:       allAlerts.filter((a) => a.status   === 'ACTIVE').length,
    ACKNOWLEDGED: allAlerts.filter((a) => a.status   === 'ACKNOWLEDGED').length,
    avgMttr: (() => {
      const resolved = allAlerts.filter((a) => a.resolvedAt && a.detectedAt);
      if (!resolved.length) return null;
      const sum = resolved.reduce((acc, a) => acc + calcMttr(a), 0);
      return Math.round(sum / resolved.length);
    })(),
  }), [allAlerts]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
      {/* KPI row */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: 1.5 }}>
        <KpiCard label="Critical"     value={counts.CRITICAL}     sub="Active critical alerts" accent="critical" icon={Clock} highlight={counts.CRITICAL > 0} />
        <KpiCard label="High"         value={counts.HIGH}         sub="High severity"          accent="high"     icon={Clock} highlight={counts.HIGH > 0} />
        <KpiCard label="Active"       value={counts.ACTIVE}       sub="Unresolved"             accent={counts.ACTIVE > 0 ? 'critical' : 'low'} icon={Clock} highlight={counts.ACTIVE > 0} />
        <KpiCard label="Acknowledged" value={counts.ACKNOWLEDGED} sub="In progress"            accent="medium"   icon={Clock} />
        <KpiCard label="Avg MTTR"     value={counts.avgMttr !== null ? `${counts.avgMttr}m` : '—'} sub="Mean time to resolve" accent="info" icon={Clock} />
      </Box>

      {/* Filters */}
      <FilterBar>
        {/* Service / endpoint search */}
        <TextField
          placeholder="Service or endpoint…"
          size="small"
          value={serviceSearch}
          onChange={(e) => setServiceSearch(e.target.value)}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <Search size={14} style={{ color: '#6b7280' }} />
                </InputAdornment>
              ),
            },
          }}
          sx={{ minWidth: 200, maxWidth: 260 }}
        />

        {/* Severity filter */}
        <ToggleButtonGroup value={severityFilter} exclusive onChange={(_, v) => v && setSeverityFilter(v)} size="small">
          <ToggleButton value="all">All</ToggleButton>
          <ToggleButton value="CRITICAL" sx={{ '&.Mui-selected': { color: '#ef4444' } }}>CRIT</ToggleButton>
          <ToggleButton value="HIGH"     sx={{ '&.Mui-selected': { color: '#f97316' } }}>HIGH</ToggleButton>
          <ToggleButton value="MEDIUM"   sx={{ '&.Mui-selected': { color: '#eab308' } }}>MED</ToggleButton>
          <ToggleButton value="LOW"      sx={{ '&.Mui-selected': { color: '#22c55e' } }}>LOW</ToggleButton>
        </ToggleButtonGroup>

        {/* Status filter */}
        <ToggleButtonGroup value={statusFilter} exclusive onChange={(_, v) => v && setStatusFilter(v)} size="small">
          <ToggleButton value="all">All Status</ToggleButton>
          <ToggleButton value="ACTIVE"      >Active</ToggleButton>
          <ToggleButton value="ACKNOWLEDGED">Acked</ToggleButton>
          <ToggleButton value="RESOLVED"    >Resolved</ToggleButton>
        </ToggleButtonGroup>

        {/* Time range */}
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel sx={{ fontSize: '0.8rem' }}>Time Range</InputLabel>
          <Select
            value={timeRange}
            label="Time Range"
            onChange={(e) => setTimeRange(e.target.value)}
            sx={{ fontSize: '0.8rem' }}
          >
            {TIME_RANGE_OPTIONS.map((o) => (
              <MenuItem key={o.value} value={o.value} sx={{ fontSize: '0.8rem' }}>{o.label}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            {filtered.length} of {allAlerts.length}
          </Typography>
          <Tooltip title="Refresh" arrow>
            <IconButton size="small" onClick={() => refetch()} disabled={isFetching}>
              <RefreshCcw size={14} style={{ animation: isFetching ? 'spin 1s linear infinite' : 'none' }} />
            </IconButton>
          </Tooltip>
        </Box>
      </FilterBar>

      {/* Table */}
      <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
        <TableContainer sx={{ maxHeight: 'calc(100dvh - 420px)' }}>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                {['ID', 'Service', 'Endpoint', 'Severity', 'Hybrid Score', 'MSIF', 'PLE', 'Status', 'Detected', 'MTTR', 'Actions'].map(
                  (col) => <TableCell key={col}>{col}</TableCell>
                )}
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <LoadingRows cols={11} rows={8} />
              ) : filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={11}>
                    <EmptyState message="No anomalies match filters" icon="✓" />
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((a) => {
                  const mttr = calcMttr(a);
                  return (
                    <TableRow key={a.id} sx={{
                      '&:hover': { bgcolor: 'action.hover' },
                      backgroundColor:
                        a.severity === 'CRITICAL' ? 'rgba(239,68,68,0.04)' :
                        a.severity === 'HIGH'     ? 'rgba(249,115,22,0.04)' :
                        'transparent',
                    }}>
                      <TableCell sx={{ fontSize: '0.7rem', color: 'text.secondary', fontFamily: 'monospace' }}>
                        #{a.id}
                      </TableCell>
                      <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'primary.main', fontWeight: 500 }}>
                        {a.apiName}
                      </TableCell>
                      <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.7rem', color: 'text.secondary', maxWidth: 130, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {a.endpoint}
                      </TableCell>
                      <TableCell><SeverityBadge severity={a.severity} /></TableCell>
                      <TableCell sx={{ minWidth: 140 }}>
                        <ScoreBar score={a.hybridEnsembleScore || 0} />
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.7rem', color: 'text.secondary', fontFamily: 'monospace' }}>
                        {(a.msifLstmScore || 0).toFixed(3)}
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.7rem', color: 'text.secondary', fontFamily: 'monospace' }}>
                        {(a.pleGruScore || 0).toFixed(3)}
                      </TableCell>
                      <TableCell><SeverityBadge severity={a.status} /></TableCell>
                      <TableCell sx={{ fontSize: '0.7rem', color: 'text.secondary', whiteSpace: 'nowrap' }}>
                        {timeAgo(a.detectedAt)}
                      </TableCell>
                      <TableCell sx={{
                        fontSize: '0.7rem',
                        fontVariantNumeric: 'tabular-nums',
                        color: mttr !== null ? (mttr > 30 ? '#f97316' : '#22c55e') : 'text.secondary',
                        whiteSpace: 'nowrap',
                      }}>
                        {mttr !== null ? `${mttr}m` : '—'}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          {!a.isAcknowledged && !a.isResolved && (
                            <Tooltip title="Acknowledge" arrow>
                              <IconButton
                                size="small"
                                onClick={() => acknowledge.mutate(a.id)}
                                disabled={acknowledge.isPending}
                                sx={{ color: 'warning.main', p: 0.5 }}
                              >
                                <CheckCircle size={14} />
                              </IconButton>
                            </Tooltip>
                          )}
                          {!a.isResolved && (
                            <Tooltip title="Resolve" arrow>
                              <IconButton
                                size="small"
                                onClick={() => resolve.mutate(a.id)}
                                disabled={resolve.isPending}
                                sx={{ color: 'success.main', p: 0.5 }}
                              >
                                <XCircle size={14} />
                              </IconButton>
                            </Tooltip>
                          )}
                          {a.isResolved && (
                            <Typography variant="caption" sx={{ color: 'text.secondary', px: 0.5 }}>
                              Closed
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>

      <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
    </Box>
  );
};

export default Alerts;
