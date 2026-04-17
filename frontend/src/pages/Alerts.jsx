import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
  ToggleButtonGroup,
  ToggleButton,
  IconButton,
  Snackbar,
  Alert,
} from '@mui/material';
import { CheckCircle, Cancel, Refresh } from '@mui/icons-material';
import { BACKEND_URL } from '@/api/http';
import { SeverityBadge, ScoreBar, timeAgo, EmptyState } from '@/components/SharedComponents';

// ── Helper ────────────────────────────────────────────────────────────────────
const proxyOrMock = async (path, mockFn) => {
  try {
    const resp = await fetch(`${BACKEND_URL}${path}`, { signal: AbortSignal.timeout(5000) });
    if (!resp.ok) throw new Error('Backend error');
    return await resp.json();
  } catch {
    return mockFn();
  }
};

const generateMockAlerts = () => {
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

export const Alerts = () => {
  const queryClient = useQueryClient();
  const [severityFilter, setSeverityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  // Fetch anomalies — try backend /api/anomalies first, fall back to mock
  const { data: anomalies, isLoading, refetch } = useQuery({
    queryKey: ['/api/proxy/alerts'],
    queryFn: () => proxyOrMock('/api/anomalies?limit=30', generateMockAlerts),
    refetchInterval: 15000,
  });

  // Acknowledge mutation
  const acknowledge = useMutation({
    mutationFn: async (id) => {
      const res = await fetch(`${BACKEND_URL}/api/anomalies/${id}/acknowledge`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed');
      return res.json();
    },
    onSuccess: () => {
      setSnackbar({ open: true, message: 'Anomaly marked as acknowledged', severity: 'success' });
      queryClient.invalidateQueries({ queryKey: ['/api/proxy/alerts'] });
    },
    onError: () =>
      setSnackbar({ open: true, message: 'Action failed — backend may be offline', severity: 'error' }),
  });

  // Resolve mutation
  const resolve = useMutation({
    mutationFn: async (id) => {
      const res = await fetch(`${BACKEND_URL}/api/anomalies/${id}/resolve`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed');
      return res.json();
    },
    onSuccess: () => {
      setSnackbar({ open: true, message: 'Anomaly marked as resolved', severity: 'success' });
      queryClient.invalidateQueries({ queryKey: ['/api/proxy/alerts'] });
    },
    onError: () =>
      setSnackbar({ open: true, message: 'Action failed — backend may be offline', severity: 'error' }),
  });

  const filtered = (anomalies || []).filter((a) => {
    const matchSev = severityFilter === 'all' || a.severity === severityFilter;
    const matchStat = statusFilter === 'all' || a.status === statusFilter;
    return matchSev && matchStat;
  });

  const counts = {
    CRITICAL: (anomalies || []).filter((a) => a.severity === 'CRITICAL').length,
    HIGH: (anomalies || []).filter((a) => a.severity === 'HIGH').length,
    ACTIVE: (anomalies || []).filter((a) => a.status === 'ACTIVE').length,
    ACKNOWLEDGED: (anomalies || []).filter((a) => a.status === 'ACKNOWLEDGED').length,
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
      {/* Summary chips */}
      <Box sx={{ display: 'flex', gap: 2 }}>
        {[
          { label: 'Critical', value: counts.CRITICAL, color: 'error.main' },
          { label: 'High',     value: counts.HIGH,     color: 'warning.main' },
          { label: 'Active',   value: counts.ACTIVE,   color: 'error.main' },
          { label: 'Acknowledged', value: counts.ACKNOWLEDGED, color: 'warning.main' },
        ].map(({ label, value, color }) => (
          <Box
            key={label}
            sx={{ flex: 1, textAlign: 'center', p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}
          >
            <Typography variant="h4" sx={{ fontWeight: 700, color }}>
              {value}
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              {label}
            </Typography>
          </Box>
        ))}
      </Box>

      {/* Filters */}
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          Filter:
        </Typography>
        <ToggleButtonGroup
          value={severityFilter}
          exclusive
          onChange={(e, v) => v && setSeverityFilter(v)}
          size="small"
        >
          <ToggleButton value="all">All</ToggleButton>
          <ToggleButton value="CRITICAL">CRITICAL</ToggleButton>
          <ToggleButton value="HIGH">HIGH</ToggleButton>
          <ToggleButton value="MEDIUM">MEDIUM</ToggleButton>
          <ToggleButton value="LOW">LOW</ToggleButton>
        </ToggleButtonGroup>
        <ToggleButtonGroup
          value={statusFilter}
          exclusive
          onChange={(e, v) => v && setStatusFilter(v)}
          size="small"
        >
          <ToggleButton value="all">All Status</ToggleButton>
          <ToggleButton value="ACTIVE">ACTIVE</ToggleButton>
          <ToggleButton value="ACKNOWLEDGED">ACKNOWLEDGED</ToggleButton>
          <ToggleButton value="RESOLVED">RESOLVED</ToggleButton>
        </ToggleButtonGroup>
        <Box sx={{ ml: 'auto' }}>
          <IconButton size="small" onClick={() => refetch()}>
            <Refresh sx={{ fontSize: 18 }} />
          </IconButton>
        </Box>
      </Box>

      {/* Table */}
      <Paper>
        <TableContainer sx={{ maxHeight: 'calc(100dvh - 400px)' }}>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                {['ID', 'Service', 'Endpoint', 'Severity', 'Hybrid Score', 'MSIF-LSTM', 'PLE-GRU', 'Status', 'Detected', 'Env', 'Actions'].map(
                  (col) => (
                    <TableCell key={col} sx={{ fontWeight: 500, fontSize: '0.75rem' }}>
                      {col}
                    </TableCell>
                  )
                )}
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 11 }).map((__, j) => (
                      <TableCell key={j}>
                        <Box sx={{ height: 12, bgcolor: 'action.hover', borderRadius: 1 }} />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={11}>
                    <EmptyState message="No anomalies match filters" />
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((a) => (
                  <TableRow
                    key={a.id}
                    sx={{
                      '&:hover': { bgcolor: 'action.hover' },
                      backgroundColor:
                        a.severity === 'CRITICAL'
                          ? 'rgba(239,68,68,0.05)'
                          : a.severity === 'HIGH'
                          ? 'rgba(249,115,22,0.05)'
                          : 'transparent',
                    }}
                  >
                    <TableCell sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>#{a.id}</TableCell>
                    <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'primary.main' }}>
                      {a.apiName}
                    </TableCell>
                    <TableCell
                      sx={{
                        fontFamily: 'monospace',
                        fontSize: '0.75rem',
                        color: 'text.secondary',
                        maxWidth: 140,
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
                      <ScoreBar score={a.hybridEnsembleScore || 0} />
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>
                      {(a.msifLstmScore || 0).toFixed(3)}
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>
                      {(a.pleGruScore || 0).toFixed(3)}
                    </TableCell>
                    <TableCell>
                      <SeverityBadge severity={a.status} />
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.75rem', color: 'text.secondary', whiteSpace: 'nowrap' }}>
                      {timeAgo(a.detectedAt)}
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="caption"
                        sx={{
                          px: 1,
                          py: 0.25,
                          borderRadius: 0.5,
                          backgroundColor:
                            a.environment === 'production'
                              ? 'rgba(59,130,246,0.15)'
                              : 'rgba(107,114,128,0.15)',
                          color: a.environment === 'production' ? '#3b82f6' : '#6b7280',
                        }}
                      >
                        {a.environment}
                      </Typography>
                    </TableCell>
                    <TableCell sx={{ textAlign: 'right' }}>
                      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                        {!a.isAcknowledged && !a.isResolved && (
                          <IconButton
                            size="small"
                            onClick={() => acknowledge.mutate(a.id)}
                            disabled={acknowledge.isPending}
                            sx={{ color: 'warning.main' }}
                            title="Acknowledge"
                          >
                            <CheckCircle sx={{ fontSize: 16 }} />
                          </IconButton>
                        )}
                        {!a.isResolved && (
                          <IconButton
                            size="small"
                            onClick={() => resolve.mutate(a.id)}
                            disabled={resolve.isPending}
                            sx={{ color: 'success.main' }}
                            title="Resolve"
                          >
                            <Cancel sx={{ fontSize: 16 }} />
                          </IconButton>
                        )}
                        {a.isResolved && (
                          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                            Closed
                          </Typography>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))
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
        <Alert
          severity={snackbar.severity}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Alerts;
