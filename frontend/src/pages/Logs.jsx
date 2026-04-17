import { useState, useRef, useEffect } from 'react';
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
  Switch,
  InputAdornment,
  IconButton,
} from '@mui/material';
import { Search as SearchIcon, RefreshCcw as RefreshIcon, ChevronDown as ArrowDownIcon } from 'lucide-react';
import { BACKEND_URL } from '@/api/http';
import { SeverityBadge, EmptyState } from '@/components/SharedComponents';

const proxyOrMock = async (path, mockFn) => {
  try {
    const resp = await fetch(`${BACKEND_URL}${path}`, { signal: AbortSignal.timeout(5000) });
    if (!resp.ok) throw new Error('Backend error');
    return await resp.json();
  } catch {
    return mockFn();
  }
};

const generateMockLogs = () => {
  const levels = ['INFO', 'WARN', 'ERROR', 'DEBUG', 'CRITICAL'];
  const services = ['api-gateway', 'payment-service', 'user-service', 'auth-service'];
  const messages = [
    'Request processed successfully',
    'High latency detected on endpoint',
    'Connection timeout to downstream service',
    'Cache miss rate elevated',
    'Database query exceeded threshold',
    'JWT token validation failed',
    'Rate limit exceeded for client',
    'Service health check failed',
  ];
  return Array.from({ length: 50 }, (_, i) => ({
    id: `log-${Date.now()}-${i}`,
    level: levels[i % 5],
    message: messages[i % 8],
    serviceName: services[i % 4],
    timestamp: new Date(Date.now() - i * 45000).toISOString(),
    traceId: `trace-${Math.random().toString(36).substr(2, 9)}`,
    environment: i % 2 === 0 ? 'production' : 'staging',
    _mock: true,
  }));
};

const LEVEL_ORDER = ['CRITICAL', 'FATAL', 'ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG'];

const levelColor = {
  CRITICAL: '#ef4444',
  FATAL:    '#ef4444',
  ERROR:    '#ef4444',
  WARN:     '#f97316',
  WARNING:  '#f97316',
  INFO:     '#3b82f6',
  DEBUG:    '#6b7280',
};

export const Logs = () => {
  const [search, setSearch] = useState('');
  const [levelFilter, setLevelFilter] = useState('all');
  const [autoScroll, setAutoScroll] = useState(false);
  const bottomRef = useRef(null);

  const { data: logs, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['/api/proxy/logs'],
    queryFn: () => proxyOrMock('/api/logs/recent?limit=50', generateMockLogs),
    refetchInterval: autoScroll ? 5000 : false,
  });

  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const filtered = (Array.isArray(logs) ? logs : []).filter((l) => {
    const matchLevel = levelFilter === 'all' || l.level?.toUpperCase() === levelFilter;
    const matchSearch =
      !search ||
      l.message?.toLowerCase().includes(search.toLowerCase()) ||
      l.serviceName?.toLowerCase().includes(search.toLowerCase()) ||
      l.traceId?.toLowerCase().includes(search.toLowerCase());
    return matchLevel && matchSearch;
  });

  const levelCounts = (Array.isArray(logs) ? logs : []).reduce((acc, l) => {
    const lvl = (l.level || 'INFO').toUpperCase();
    acc[lvl] = (acc[lvl] || 0) + 1;
    return acc;
  }, {});

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
      {/* Level summary */}
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        {LEVEL_ORDER.slice(0, 6).map((lvl) => (
          <Box
            key={lvl}
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              px: 1.5,
              py: 1,
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 1,
            }}
          >
            <Typography variant="caption" sx={{ fontWeight: 500, color: levelColor[lvl] }}>
              {lvl}
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontVariantNumeric: 'tabular-nums' }}>
              {levelCounts[lvl] || 0}
            </Typography>
          </Box>
        ))}
      </Box>

      {/* Controls */}
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <TextField
          placeholder="Search messages, services, trace IDs…"
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
          value={levelFilter}
          exclusive
          onChange={(e, v) => v && setLevelFilter(v)}
          size="small"
        >
          <ToggleButton value="all">All</ToggleButton>
          <ToggleButton value="ERROR">ERROR</ToggleButton>
          <ToggleButton value="WARN">WARN</ToggleButton>
          <ToggleButton value="INFO">INFO</ToggleButton>
          <ToggleButton value="DEBUG">DEBUG</ToggleButton>
        </ToggleButtonGroup>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 'auto' }}>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            Live tail
          </Typography>
          <Switch
            checked={autoScroll}
            onChange={(e) => setAutoScroll(e.target.checked)}
            size="small"
          />
          <IconButton size="small" onClick={() => refetch()} disabled={isFetching}>
            <RefreshIcon
              size={16}
              style={{
                animation: isFetching ? 'spin 1s linear infinite' : 'none',
              }}
            />
          </IconButton>
        </Box>
      </Box>

      {/* Log table */}
      <Paper>
        <Box
          sx={{
            px: 2,
            py: 1,
            borderBottom: '1px solid',
            borderColor: 'divider',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Typography variant="caption" sx={{ color: 'text.secondary', fontFamily: 'monospace' }}>
            {filtered.length} entries {search || levelFilter !== 'all' ? '(filtered)' : ''}
          </Typography>
          {autoScroll && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: 'primary.main' }}>
              <Box
                sx={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  bgcolor: 'primary.main',
                  animation: 'pulse 2s infinite',
                  '@keyframes pulse': {
                    '0%, 100%': { opacity: 1 },
                    '50%': { opacity: 0.4 },
                  },
                }}
              />
              <Typography variant="caption">Streaming</Typography>
            </Box>
          )}
        </Box>
        <TableContainer sx={{ maxHeight: 'calc(100dvh - 340px)' }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 500, fontSize: '0.75rem', width: 100 }}>Time</TableCell>
                <TableCell sx={{ fontWeight: 500, fontSize: '0.75rem', width: 70 }}>Level</TableCell>
                <TableCell sx={{ fontWeight: 500, fontSize: '0.75rem', width: 120 }}>Service</TableCell>
                <TableCell sx={{ fontWeight: 500, fontSize: '0.75rem' }}>Message</TableCell>
                <TableCell sx={{ fontWeight: 500, fontSize: '0.75rem', width: 120 }}>Trace ID</TableCell>
                <TableCell sx={{ fontWeight: 500, fontSize: '0.75rem', width: 80 }}>Env</TableCell>
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
                    <EmptyState message="No log entries found" />
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((l, i) => (
                  <TableRow key={`${l.id}-${i}`} sx={{ '&:hover': { bgcolor: 'action.hover' } }}>
                    <TableCell
                      sx={{ fontSize: '0.75rem', color: 'text.secondary', whiteSpace: 'nowrap', fontFamily: 'monospace' }}
                    >
                      {new Date(l.timestamp).toLocaleTimeString()}
                    </TableCell>
                    <TableCell
                      sx={{
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        color: levelColor[(l.level || 'INFO').toUpperCase()] || '#6b7280',
                      }}
                    >
                      {(l.level || 'INFO').toUpperCase()}
                    </TableCell>
                    <TableCell
                      sx={{
                        fontSize: '0.75rem',
                        color: 'primary.main',
                        maxWidth: 120,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {l.serviceName}
                    </TableCell>
                    <TableCell
                      sx={{ fontSize: '0.75rem', maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis' }}
                      title={l.message}
                    >
                      {l.message}
                    </TableCell>
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
                      {l.traceId || '—'}
                    </TableCell>
                    <TableCell>
                      <SeverityBadge severity={l.environment || 'unknown'} />
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <div ref={bottomRef} />
      </Paper>

      {autoScroll && (
        <Box sx={{ display: 'flex', justifyContent: 'center' }}>
          <IconButton size="small" onClick={() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' })}>
            <ArrowDownIcon size={16} />
          </IconButton>
        </Box>
      )}

      {/* CSS keyframes for spin animation */}
      <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
    </Box>
  );
};

export default Logs;
