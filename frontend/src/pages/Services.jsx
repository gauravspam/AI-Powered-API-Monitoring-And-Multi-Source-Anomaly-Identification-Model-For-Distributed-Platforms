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
import { Search as SearchIcon } from 'lucide-react';
import { BACKEND_URL } from '@/api/http';
import { SeverityBadge, StatusDot, EmptyState } from '@/components/SharedComponents';

const proxyOrMock = async (path, mockFn) => {
  try {
    const resp = await fetch(`${BACKEND_URL}${path}`, { signal: AbortSignal.timeout(5000) });
    if (!resp.ok) throw new Error('Backend error');
    return await resp.json();
  } catch {
    return mockFn();
  }
};

const generateMockServices = () => [
  { id: 1, name: 'api-gateway',          ownerTeam: 'Platform',   environment: 'production', status: 'healthy',  avgLatencyMs: 45,  errorRate: 0.02,  anomalyRate: 0.10, requestPerMin: 1200 },
  { id: 2, name: 'payment-service',       ownerTeam: 'Commerce',   environment: 'production', status: 'degraded', avgLatencyMs: 312, errorRate: 0.08,  anomalyRate: 0.40, requestPerMin: 340  },
  { id: 3, name: 'user-service',          ownerTeam: 'Identity',   environment: 'production', status: 'healthy',  avgLatencyMs: 67,  errorRate: 0.01,  anomalyRate: 0.05, requestPerMin: 890  },
  { id: 4, name: 'auth-service',          ownerTeam: 'Identity',   environment: 'production', status: 'healthy',  avgLatencyMs: 38,  errorRate: 0.005, anomalyRate: 0.02, requestPerMin: 2100 },
  { id: 5, name: 'notification-service',  ownerTeam: 'Comm',       environment: 'staging',    status: 'healthy',  avgLatencyMs: 95,  errorRate: 0.03,  anomalyRate: 0.15, requestPerMin: 450  },
  { id: 6, name: 'inventory-service',     ownerTeam: 'Commerce',   environment: 'production', status: 'healthy',  avgLatencyMs: 112, errorRate: 0.02,  anomalyRate: 0.08, requestPerMin: 220  },
  { id: 7, name: 'analytics-service',     ownerTeam: 'Data',       environment: 'production', status: 'degraded', avgLatencyMs: 890, errorRate: 0.12,  anomalyRate: 0.55, requestPerMin: 180  },
  { id: 8, name: 'search-service',        ownerTeam: 'Discovery',  environment: 'production', status: 'healthy',  avgLatencyMs: 78,  errorRate: 0.01,  anomalyRate: 0.06, requestPerMin: 760  },
];

export const Services = () => {
  const [search, setSearch] = useState('');
  const [envFilter, setEnvFilter] = useState('all');

  const { data: services, isLoading } = useQuery({
    queryKey: ['/api/proxy/services'],
    queryFn: () => proxyOrMock('/api/services', generateMockServices),
    refetchInterval: 30000,
  });

  const filtered = (services || []).filter((s) => {
    const matchSearch =
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.ownerTeam.toLowerCase().includes(search.toLowerCase());
    const matchEnv = envFilter === 'all' || s.environment === envFilter;
    return matchSearch && matchEnv;
  });

  const healthy = (services || []).filter((s) => s.status === 'healthy').length;
  const degraded = (services || []).filter((s) => s.status === 'degraded').length;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
      {/* Summary chips */}
      <Box sx={{ display: 'flex', gap: 2 }}>
        {[
          { label: 'Total Services', value: (services || []).length,     color: 'text.primary' },
          { label: 'Healthy',        value: healthy,                       color: 'success.main' },
          { label: 'Degraded',       value: degraded,                      color: 'warning.main' },
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

      {/* Filters */}
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
        <TextField
          placeholder="Search services…"
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
          sx={{ minWidth: 250 }}
        />
        <ToggleButtonGroup
          value={envFilter}
          exclusive
          onChange={(e, v) => v && setEnvFilter(v)}
          size="small"
        >
          <ToggleButton value="all">All Envs</ToggleButton>
          <ToggleButton value="production">Production</ToggleButton>
          <ToggleButton value="staging">Staging</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Table */}
      <Paper>
        <TableContainer sx={{ maxHeight: 'calc(100dvh - 340px)' }}>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                {[
                  { label: 'Service',      align: 'left'  },
                  { label: 'Team',         align: 'left'  },
                  { label: 'Environment',  align: 'left'  },
                  { label: 'Status',       align: 'left'  },
                  { label: 'Avg Latency',  align: 'right' },
                  { label: 'Error Rate',   align: 'right' },
                  { label: 'Anomaly Rate', align: 'right' },
                  { label: 'Req/min',      align: 'right' },
                ].map(({ label, align }) => (
                  <TableCell key={label} align={align} sx={{ fontWeight: 500, fontSize: '0.75rem' }}>
                    {label}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 8 }).map((__, j) => (
                      <TableCell key={j}>
                        <Box sx={{ height: 12, bgcolor: 'action.hover', borderRadius: 1 }} />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8}>
                    <EmptyState message="No services found" />
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
                      <Typography
                        variant="caption"
                        sx={{
                          px: 1,
                          py: 0.25,
                          borderRadius: 0.5,
                          backgroundColor:
                            s.environment === 'production'
                              ? 'rgba(59,130,246,0.15)'
                              : 'rgba(107,114,128,0.15)',
                          color: s.environment === 'production' ? '#3b82f6' : '#6b7280',
                        }}
                      >
                        {s.environment}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <StatusDot status={s.status} />
                        <Typography variant="caption" sx={{ textTransform: 'capitalize' }}>
                          {s.status}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell
                      align="right"
                      sx={{
                        fontSize: '0.75rem',
                        color:
                          s.avgLatencyMs > 500 ? 'warning.main' :
                          s.avgLatencyMs > 200 ? '#eab308' :
                          'text.primary',
                      }}
                    >
                      {s.avgLatencyMs}ms
                    </TableCell>
                    <TableCell
                      align="right"
                      sx={{
                        fontSize: '0.75rem',
                        color:
                          s.errorRate > 0.1 ? 'error.main' :
                          s.errorRate > 0.05 ? 'warning.main' :
                          'text.primary',
                      }}
                    >
                      {(s.errorRate * 100).toFixed(1)}%
                    </TableCell>
                    <TableCell
                      align="right"
                      sx={{
                        fontSize: '0.75rem',
                        color:
                          s.anomalyRate > 0.4 ? 'error.main' :
                          s.anomalyRate > 0.2 ? 'warning.main' :
                          'text.primary',
                      }}
                    >
                      {(s.anomalyRate * 100).toFixed(0)}%
                    </TableCell>
                    <TableCell align="right" sx={{ fontSize: '0.75rem' }}>
                      {s.requestPerMin.toLocaleString()}
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
