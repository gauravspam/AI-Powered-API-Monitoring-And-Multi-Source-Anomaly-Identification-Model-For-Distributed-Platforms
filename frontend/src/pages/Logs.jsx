import { useState, useRef, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box, Paper, Typography, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, TextField, ToggleButtonGroup, ToggleButton, Switch,
  InputAdornment, IconButton, MenuItem, Select, FormControl, InputLabel, Tooltip,
} from '@mui/material';
import { Search, RefreshCcw, ChevronDown, FileText } from 'lucide-react';
import { BACKEND_URL } from '@/api/http';
import { EmptyState, LoadingRows, KpiCard, FilterBar } from '@/components/SharedComponents';

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

const MOCK_MESSAGES = [
  'Request processed successfully',
  'High latency detected on endpoint /api/orders',
  'Connection timeout to downstream auth-service',
  'Cache miss rate elevated — hitting DB fallback',
  'Database query exceeded 500ms threshold',
  'JWT token validation failed for client 192.168.1.45',
  'Rate limit exceeded for client IP 10.0.0.12',
  'Health check failed — circuit breaker tripped',
  'Retry attempt 3/5 for upstream payment gateway',
  'Memory heap approaching limit (82% used)',
];

const generateMockLogs = () => {
  const levels   = ['INFO', 'WARN', 'ERROR', 'DEBUG', 'CRITICAL', 'FATAL'];
  const services = ['api-gateway', 'payment-service', 'user-service', 'auth-service', 'analytics-service'];
  return Array.from({ length: 60 }, (_, i) => ({
    id: `log-${Date.now()}-${i}`,
    level: levels[i % levels.length],
    message: MOCK_MESSAGES[i % MOCK_MESSAGES.length],
    serviceName: services[i % services.length],
    timestamp: new Date(Date.now() - i * 45000).toISOString(),
    traceId: `trace-${Math.random().toString(36).substr(2, 9)}`,
    _mock: true,
  }));
};

const LEVEL_ORDER  = ['CRITICAL', 'FATAL', 'ERROR', 'WARN', 'INFO', 'DEBUG'];
const LEVEL_COLORS = {
  CRITICAL: '#ef4444',
  FATAL:    '#ef4444',
  ERROR:    '#ef4444',
  WARN:     '#f97316',
  WARNING:  '#f97316',
  INFO:     '#3b82f6',
  DEBUG:    '#6b7280',
};

const TIME_RANGE_OPTIONS = [
  { label: 'Last 15m', value: 15  },
  { label: 'Last 1h',  value: 60  },
  { label: 'Last 6h',  value: 360 },
  { label: 'Last 24h', value: 1440 },
  { label: 'All',      value: 0   },
];

export const Logs = () => {
  const [search,      setSearch]      = useState('');
  const [levelFilter, setLevelFilter] = useState('all');
  const [serviceFilter, setServiceFilter] = useState('all');
  const [timeRange,   setTimeRange]   = useState(0);
  const [autoScroll,  setAutoScroll]  = useState(false);
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

  const allLogs = useMemo(() => (Array.isArray(logs) ? logs : []), [logs]);

  const services = useMemo(() => {
    const s = [...new Set(allLogs.map((l) => l.serviceName).filter(Boolean))].sort();
    return ['all', ...s];
  }, [allLogs]);

  const filtered = useMemo(() => {
    const now = Date.now();
    const cutoff = timeRange > 0 ? now - timeRange * 60 * 1000 : 0;
    return allLogs.filter((l) => {
      const lvl = (l.level || 'INFO').toUpperCase();
      const matchLevel   = levelFilter   === 'all' || lvl === levelFilter;
      const matchService = serviceFilter === 'all' || l.serviceName === serviceFilter;
      const matchSearch  = !search ||
        l.message?.toLowerCase().includes(search.toLowerCase()) ||
        l.serviceName?.toLowerCase().includes(search.toLowerCase()) ||
        l.traceId?.toLowerCase().includes(search.toLowerCase());
      const matchTime = timeRange === 0 || new Date(l.timestamp).getTime() >= cutoff;
      return matchLevel && matchService && matchSearch && matchTime;
    });
  }, [allLogs, levelFilter, serviceFilter, search, timeRange]);

  const levelCounts = useMemo(() =>
    allLogs.reduce((acc, l) => {
      const lvl = (l.level || 'INFO').toUpperCase();
      acc[lvl] = (acc[lvl] || 0) + 1;
      return acc;
    }, {}), [allLogs]);

  const errorCount = (levelCounts['CRITICAL'] || 0) + (levelCounts['FATAL'] || 0) + (levelCounts['ERROR'] || 0);
  const warnCount  = (levelCounts['WARN'] || 0) + (levelCounts['WARNING'] || 0);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
      {/* Level summary KPIs */}
      <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
        <KpiCard label="Error / Fatal / Critical" value={errorCount} sub="Log-level errors" accent={errorCount > 0 ? 'critical' : 'low'} icon={FileText} highlight={errorCount > 0} />
        <KpiCard label="Warnings" value={warnCount} sub="WARN level" accent={warnCount > 5 ? 'high' : 'low'} icon={FileText} />
        <KpiCard label="Total Entries" value={allLogs.length} sub="Current window" accent="info" icon={FileText} />
        {LEVEL_ORDER.slice(0, 5).map((lvl) => (
          <Box
            key={lvl}
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              px: 1.5,
              py: 1,
              border: '1px solid',
              borderRadius: 1.5,
              cursor: 'pointer',
              backgroundColor: levelFilter === lvl ? `${LEVEL_COLORS[lvl]}15` : 'transparent',
              borderColor: levelFilter === lvl ? `${LEVEL_COLORS[lvl]}50` : 'divider',
              '&:hover': { backgroundColor: `${LEVEL_COLORS[lvl]}10` },
              transition: 'all 0.15s',
            }}
            onClick={() => setLevelFilter(levelFilter === lvl ? 'all' : lvl)}
          >
            <Typography variant="caption" sx={{ fontWeight: 600, color: LEVEL_COLORS[lvl], fontSize: '0.7rem' }}>
              {lvl}
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontVariantNumeric: 'tabular-nums', fontSize: '0.7rem' }}>
              {levelCounts[lvl] || 0}
            </Typography>
          </Box>
        ))}
      </Box>

      {/* Filters */}
      <FilterBar>
        <TextField
          placeholder="Search message, service, trace ID…"
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
          sx={{ minWidth: 240, maxWidth: 320 }}
        />

        {/* Level filter */}
        <ToggleButtonGroup value={levelFilter} exclusive onChange={(_, v) => v && setLevelFilter(v)} size="small">
          <ToggleButton value="all">All</ToggleButton>
          <ToggleButton value="ERROR"    sx={{ '&.Mui-selected': { color: '#ef4444' } }}>ERROR</ToggleButton>
          <ToggleButton value="WARN"     sx={{ '&.Mui-selected': { color: '#f97316' } }}>WARN</ToggleButton>
          <ToggleButton value="INFO"     sx={{ '&.Mui-selected': { color: '#3b82f6' } }}>INFO</ToggleButton>
          <ToggleButton value="DEBUG"    sx={{ '&.Mui-selected': { color: '#6b7280' } }}>DEBUG</ToggleButton>
          <ToggleButton value="CRITICAL" sx={{ '&.Mui-selected': { color: '#ef4444' } }}>CRIT</ToggleButton>
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
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>Live tail</Typography>
          <Switch checked={autoScroll} onChange={(e) => setAutoScroll(e.target.checked)} size="small" />
          <Tooltip title="Refresh" arrow>
            <IconButton size="small" onClick={() => refetch()} disabled={isFetching}>
              <RefreshCcw size={14} style={{ animation: isFetching ? 'spin 1s linear infinite' : 'none' }} />
            </IconButton>
          </Tooltip>
        </Box>
      </FilterBar>

      {/* Log stream */}
      <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
        <Box sx={{
          px: 2, py: 1,
          borderBottom: '1px solid', borderColor: 'divider',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <Typography variant="caption" sx={{ color: 'text.secondary', fontFamily: 'monospace' }}>
            {filtered.length} entries {(search || levelFilter !== 'all' || serviceFilter !== 'all') ? '(filtered)' : ''}
          </Typography>
          {autoScroll && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
              <Box sx={{
                width: 6, height: 6, borderRadius: '50%', bgcolor: 'primary.main',
                animation: 'livePulse 1.5s ease-in-out infinite',
                '@keyframes livePulse': {
                  '0%, 100%': { opacity: 1 },
                  '50%': { opacity: 0.3 },
                },
              }} />
              <Typography variant="caption" sx={{ color: 'primary.main', fontSize: '0.7rem' }}>Streaming</Typography>
            </Box>
          )}
        </Box>
        <TableContainer sx={{ maxHeight: 'calc(100dvh - 420px)' }}>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell sx={{ width: 105 }}>Time</TableCell>
                <TableCell sx={{ width: 72 }}>Level</TableCell>
                <TableCell sx={{ width: 130 }}>Service</TableCell>
                <TableCell>Message</TableCell>
                <TableCell sx={{ width: 120 }}>Trace ID</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <LoadingRows cols={5} rows={8} />
              ) : filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5}>
                    <EmptyState message="No log entries found" />
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((l, i) => {
                  const lvl = (l.level || 'INFO').toUpperCase();
                  const color = LEVEL_COLORS[lvl] || '#6b7280';
                  return (
                    <TableRow key={`${l.id}-${i}`} sx={{
                      '&:hover': { bgcolor: 'action.hover' },
                      backgroundColor:
                        lvl === 'CRITICAL' || lvl === 'FATAL' ? 'rgba(239,68,68,0.04)' :
                        lvl === 'ERROR'                       ? 'rgba(239,68,68,0.02)' :
                        'transparent',
                    }}>
                      <TableCell sx={{ fontSize: '0.7rem', color: 'text.secondary', whiteSpace: 'nowrap', fontFamily: 'monospace' }}>
                        {new Date(l.timestamp).toLocaleTimeString()}
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.7rem', fontWeight: 700, color }}>
                        {lvl}
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.7rem', color: 'primary.main', maxWidth: 130, overflow: 'hidden', textOverflow: 'ellipsis', fontFamily: 'monospace' }}>
                        {l.serviceName}
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.75rem', maxWidth: 420, overflow: 'hidden', textOverflow: 'ellipsis' }} title={l.message}>
                        {l.message}
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.7rem', color: 'text.secondary', maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', fontFamily: 'monospace' }}>
                        {l.traceId || '—'}
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <div ref={bottomRef} />
      </Paper>

      {autoScroll && (
        <Box sx={{ display: 'flex', justifyContent: 'center' }}>
          <Tooltip title="Jump to latest" arrow>
            <IconButton size="small" onClick={() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' })}>
              <ChevronDown size={16} />
            </IconButton>
          </Tooltip>
        </Box>
      )}

      <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
    </Box>
  );
};

export default Logs;
