import { useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Button,
  Slider,
  LinearProgress,
  Snackbar,
  Alert,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Speed as SpeedIcon,
  Send as SendIcon,
  Refresh as RefreshIcon,
  CheckCircle,
  Warning,
  KeyboardArrowUp,
  KeyboardArrowDown,
} from '@mui/icons-material';
import { ML_SERVICE_URL, BACKEND_URL } from '@/api/http';
import { SeverityBadge, ScoreBar, timeAgo, EmptyState } from '@/components/SharedComponents';

// ── Constants ─────────────────────────────────────────────────────────────────
const SEVERITY_OPTIONS = [
  { label: 'Normal',   value: 'NORMAL',   score: 0.05, description: 'CPU ~25%, Mem ~35%, Latency ~120ms, Error 1%' },
  { label: 'Low',      value: 'LOW',      score: 0.28, description: 'CPU ~45%, Mem ~55%, Latency ~350ms, Error 5%' },
  { label: 'Medium',   value: 'MEDIUM',   score: 0.52, description: 'CPU ~65%, Mem ~70%, Latency ~900ms, Error 15%' },
  { label: 'High',     value: 'HIGH',     score: 0.73, description: 'CPU ~82%, Mem ~85%, Latency ~2.5s, Error 30%' },
  { label: 'Critical', value: 'CRITICAL', score: 0.91, description: 'CPU ~95%, Mem ~92%, Latency ~5.5s, Error 60%' },
];

const SEVERITY_COLORS = {
  NORMAL:   '#6b7280',
  LOW:      '#22c55e',
  MEDIUM:   '#eab308',
  HIGH:     '#f97316',
  CRITICAL: '#ef4444',
};

// Metric values used when building the ML request payload
const SEVERITY_METRICS = {
  NORMAL:   { cpu: 25, mem: 35, rt: 120,  err: 1  },
  LOW:      { cpu: 45, mem: 55, rt: 350,  err: 5  },
  MEDIUM:   { cpu: 65, mem: 70, rt: 900,  err: 15 },
  HIGH:     { cpu: 82, mem: 85, rt: 2500, err: 30 },
  CRITICAL: { cpu: 95, mem: 92, rt: 5500, err: 60 },
};

const LS_KEY = 'simulator_history';

// ── LocalStorage helpers ──────────────────────────────────────────────────────
function loadHistory() {
  try {
    const raw = localStorage.getItem(LS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveHistory(history) {
  try {
    // Keep only last 50 entries
    localStorage.setItem(LS_KEY, JSON.stringify(history.slice(0, 50)));
  } catch {
    // localStorage may be full — ignore silently
  }
}

function normalizeToArray(value) {
  if (!value) return [];
  return Array.isArray(value) ? value : [value];
}

function buildBackendPayload(payload, selectedSeverity) {
  const now = new Date();
  const metrics = Array.isArray(payload.metrics) ? payload.metrics[0] : payload.metrics || {};
  const severityStatusCode = {
    NORMAL: 200,
    LOW: 200,
    MEDIUM: 429,
    HIGH: 500,
    CRITICAL: 503,
  };

  return {
    apiName: '/simulator/signal',
    method: 'POST',
    responseTime: Number(metrics.response_time_ms ?? 0),
    statusCode: severityStatusCode[selectedSeverity] ?? 200,
    requestCount: Number(metrics.request_count ?? 1),
    errorRate: (() => {
      const value = Number(metrics.error_rate ?? 0);
      return Math.max(0, Math.min(1, value > 1 ? value / 100 : value));
    })(),
    cpuUsage: Number(metrics.cpu_usage ?? 0),
    memoryUsage: Number(metrics.memory_usage ?? 0),
    networkIo: Number(metrics.network_io ?? 0),
    diskIo: Number(metrics.disk_io ?? 0),
    hourOfDay: now.getHours(),
    dayOfWeek: ((now.getDay() + 6) % 7) + 1,
    timestamp: now.toISOString(),
    environment: 'development',
    serviceName: 'frontend-simulator',
    logs: normalizeToArray(payload.logs),
    traces: normalizeToArray(payload.traces),
    metrics,
  };
}

// ── Modality control ──────────────────────────────────────────────────────────
function ModalityControl({ icon: _Icon, label, description, count, setCount, enabled, setEnabled, color }) {
  const Icon = _Icon;
  return (
    <Paper
      sx={{
        p: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 1.5,
        border: '1px solid',
        borderColor: enabled ? 'primary.main' : 'divider',
        opacity: enabled ? 1 : 0.6,
        mb: 2,
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Icon sx={{ fontSize: 18, color }} />
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {label}
          </Typography>
          <Typography
            variant="caption"
            sx={{
              px: 1,
              py: 0.25,
              borderRadius: 0.5,
              backgroundColor: enabled ? 'rgba(59,130,246,0.15)' : 'rgba(107,114,128,0.15)',
              color: enabled ? '#3b82f6' : '#6b7280',
              fontFamily: 'monospace',
            }}
          >
            {enabled ? count : 0}
          </Typography>
        </Box>
        <Button
          size="small"
          variant={enabled ? 'contained' : 'outlined'}
          onClick={() => setEnabled(!enabled)}
          sx={{ fontSize: '0.75rem', py: 0.5 }}
        >
          {enabled ? 'Enabled' : 'Disabled'}
        </Button>
      </Box>
      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
        {description}
      </Typography>
      {enabled && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              Count
            </Typography>
            <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
              {count}
            </Typography>
          </Box>
          <Slider value={count} onChange={(e, v) => setCount(v)} min={1} max={20} step={1} size="small" />
          <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.625rem', color: 'text.secondary' }}>
            <span>1</span>
            <span>20</span>
          </Box>
        </Box>
      )}
    </Paper>
  );
}

// ── Page component ─────────────────────────────────────────────────────────────
export const Simulator = () => {
  const queryClient = useQueryClient();
  const [severity, setSeverity] = useState('MEDIUM');
  const [metricsEnabled, setMetricsEnabled] = useState(true);
  const [logsEnabled, setLogsEnabled] = useState(true);
  const [tracesEnabled, setTracesEnabled] = useState(true);
  const [metricsCount, setMetricsCount] = useState(1);
  const [logsCount, setLogsCount] = useState(5);
  const [tracesCount, setTracesCount] = useState(3);
  const [lastResult, setLastResult] = useState(null);
  const [isPending, setIsPending] = useState(false);
  const [expandedRow, setExpandedRow] = useState(null);
  const [history, setHistory] = useState(loadHistory);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [sendViaBackend, setSendViaBackend] = useState(true);

  const activeModalities = [metricsEnabled, logsEnabled, tracesEnabled].filter(Boolean).length;
  const selectedSev = SEVERITY_OPTIONS.find((s) => s.value === severity);

  // ── Build ML request payload ────────────────────────────────────────────────
  const buildPayload = useCallback(() => {
    const m = SEVERITY_METRICS[severity];
    const payload = { severity };

    if (metricsEnabled) {
      const metricEntry = {
        cpu_usage: m.cpu,
        memory_usage: m.mem,
        response_time_ms: m.rt,
        error_rate: m.err / 100,
        request_count: 100 + Math.floor(Math.random() * 900),
        service_id: 'service-1',
      };
      if (metricsCount > 1) {
        payload.metrics = Array.from({ length: metricsCount }, (_, i) => ({
          ...metricEntry,
          service_id: `service-${(i % 4) + 1}`,
        }));
      } else {
        payload.metrics = metricEntry;
      }
    }

    if (logsEnabled) {
      const logLevels = { NORMAL: 'INFO', LOW: 'WARNING', MEDIUM: 'ERROR', HIGH: 'ERROR', CRITICAL: 'FATAL' };
      payload.logs = Array.from({ length: logsCount }, (_, i) => ({
        level: logLevels[severity],
        message: `[${severity}] Synthetic log entry #${i + 1}`,
        service: `service-${(i % 4) + 1}`,
        timestamp: new Date().toISOString(),
      }));
    }

    if (tracesEnabled) {
      payload.traces = Array.from({ length: tracesCount }, (_, i) => ({
        trace_id: `trace-${Date.now()}-${i}`,
        span_id: `span-${i}`,
        service: `service-${(i % 4) + 1}`,
        operation: 'http.request',
        duration_ms: m.rt + Math.floor(Math.random() * 200),
        latency_ms: m.rt + Math.floor(Math.random() * 200),
        duration: m.rt + Math.floor(Math.random() * 200),
        status_code: severity === 'CRITICAL' || severity === 'HIGH' ? 500 : 200,
        status: severity === 'CRITICAL' ? 'timeout' : severity === 'HIGH' ? 'error' : 'ok',
      }));
    }

    return payload;
  }, [severity, metricsEnabled, logsEnabled, tracesEnabled, metricsCount, logsCount, tracesCount]);

  // ── Send to ML service ──────────────────────────────────────────────────────
  const handleSimulate = async () => {
    if (activeModalities === 0 || isPending) return;
    setIsPending(true);

    const runId = Date.now();
    const startedAt = new Date().toISOString();

    // Optimistic history entry
    const pending = {
      id: runId,
      timestamp: startedAt,
      route: sendViaBackend ? 'backend' : 'ml-service',
      severity,
      metricsCount: metricsEnabled ? metricsCount : 0,
      logsCount: logsEnabled ? logsCount : 0,
      tracesCount: tracesEnabled ? tracesCount : 0,
      status: 'running',
      hybridScore: null,
      msifScore: null,
      pleScore: null,
      finalSeverity: null,
      responsePayload: null,
      error: null,
    };

    const newHistory = [pending, ...history];
    setHistory(newHistory);
    saveHistory(newHistory);

    let mlResult = null;
    let isMock = false;
    let errorMsg = null;

    try {
      const payload = buildPayload();

      if (sendViaBackend) {
        const backendPayload = buildBackendPayload(payload, severity);
        const resp = await fetch(`${BACKEND_URL}/api/anomalies/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(backendPayload),
          signal: AbortSignal.timeout(12000),
        });

        if (!resp.ok) throw new Error(`Backend service responded with ${resp.status}`);
        const backendResult = await resp.json();

        const backendScore =
          backendResult.final_anomaly_score ??
          backendResult.finalAnomalyScore ??
          backendResult.hybrid_ensemble_score ??
          backendResult.hybridEnsembleScore ??
          selectedSev.score;

        mlResult = {
          final_score: backendScore,
          hybrid_score: backendScore,
          msif_score: null,
          ple_score: null,
          severity: backendResult.severity ?? severity,
          confidence: backendResult.confidence ?? (activeModalities / 3),
          fusion_method: backendResult.source ?? 'backend-analysis',
          _backend: true,
          backend_response: backendResult,
        };
      } else {
        const resp = await fetch(`${ML_SERVICE_URL}/predict/flexible`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
          signal: AbortSignal.timeout(10000),
        });

        if (!resp.ok) throw new Error(`ML service responded with ${resp.status}`);
        mlResult = await resp.json();
      }
    } catch (err) {
      // Service unavailable - fallback to mock result
      isMock = true;
      errorMsg = err.message;
      const base = selectedSev.score;
      mlResult = {
        hybrid_score: base + (Math.random() - 0.5) * 0.08,
        msif_score: base + (Math.random() - 0.5) * 0.1,
        ple_score: base + (Math.random() - 0.5) * 0.1,
        severity: severity,
        confidence: activeModalities / 3,
        fusion_method: 'weighted_ensemble',
        _mock: true,
        _backend: sendViaBackend,
      };
    }

    const hybridScore = mlResult.hybrid_score ?? mlResult.final_score ?? selectedSev.score;

    // Update history entry
    const completedEntry = {
      ...pending,
      status: isMock ? 'completed_mock' : 'completed',
      hybridScore,
      msifScore: mlResult.msif_score ?? null,
      pleScore: mlResult.ple_score ?? null,
      finalSeverity: mlResult.severity ?? severity,
      responsePayload: JSON.stringify(mlResult),
      error: errorMsg,
    };

    const updated = newHistory.map((h) => (h.id === runId ? completedEntry : h));
    setHistory(updated);
    saveHistory(updated);

    setLastResult({ mlResult, warning: isMock ? errorMsg : null });

    if (isMock) {
      setSnackbar({
        open: true,
        message: `Simulation complete (Mock): ${sendViaBackend ? 'backend' : 'ML service'} unavailable`,
        severity: 'warning',
      });
    } else {
      if (sendViaBackend) {
        queryClient.invalidateQueries({ queryKey: ['/api/proxy/alerts'] });
        queryClient.invalidateQueries({ queryKey: ['/api/proxy/anomalies'] });
        queryClient.invalidateQueries({ queryKey: ['/api/proxy/overview'] });
        queryClient.invalidateQueries({ queryKey: ['/api/sidebar/badge'] });
      }
      setSnackbar({
        open: true,
        message: `${sendViaBackend ? 'Backend' : 'ML service'} returned severity: ${mlResult.severity}`,
        severity: 'success',
      });
    }

    setIsPending(false);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Info banner */}
      <Paper sx={{ p: 2, display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
        <SpeedIcon sx={{ color: 'primary.main', mt: 0.5 }} />
        <Box>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            Signal Simulator
          </Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            Send synthetic telemetry signals (metrics, logs, traces) either directly to ML or through backend.
            Backend mode persists anomalies and can trigger alerts via{' '}
            <Typography component="span" sx={{ fontFamily: 'monospace', color: 'primary.main' }}>
              POST /api/anomalies/analyze
            </Typography>
            . Direct mode uses{' '}
            <Typography component="span" sx={{ fontFamily: 'monospace', color: 'primary.main' }}>
              POST /predict/flexible
            </Typography>
            . History is stored locally in this browser.
          </Typography>
        </Box>
      </Paper>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
        {/* Left column: severity + score + send */}
        <Box sx={{ flex: '1 1 280px', minWidth: 250 }}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 2, mb: 2 }}>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              Severity Level
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {SEVERITY_OPTIONS.map((opt) => (
                <Button
                  key={opt.value}
                  onClick={() => setSeverity(opt.value)}
                  variant={severity === opt.value ? 'contained' : 'outlined'}
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    py: 1.5,
                    borderColor: severity === opt.value ? 'primary.main' : 'divider',
                    backgroundColor: severity === opt.value ? 'action.selected' : 'transparent',
                  }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                    <Typography
                      variant="body2"
                      sx={{
                        fontWeight: 500,
                        color: severity === opt.value ? SEVERITY_COLORS[opt.value] : 'text.primary',
                      }}
                    >
                      {opt.label}
                    </Typography>
                    <Typography variant="caption" sx={{ fontFamily: 'monospace', color: 'text.secondary' }}>
                      {opt.score.toFixed(2)}
                    </Typography>
                  </Box>
                  <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.625rem' }}>
                    {opt.description}
                  </Typography>
                </Button>
              ))}
            </Box>
          </Paper>

          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 1.5, mb: 2 }}>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              Expected Score
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                Hybrid Score
              </Typography>
              <Typography variant="caption" sx={{ fontFamily: 'monospace', color: SEVERITY_COLORS[severity] }}>
                ~{selectedSev.score.toFixed(2)}
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={selectedSev.score * 100}
              sx={{
                height: 8,
                borderRadius: 4,
                bgcolor: 'action.hover',
                '& .MuiLinearProgress-bar': { backgroundColor: SEVERITY_COLORS[severity] },
              }}
            />
            <Box sx={{ display: 'flex', gap: 1.5 }}>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                Confidence:
              </Typography>
              <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                {(activeModalities / 3).toFixed(2)}
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                ({activeModalities}/3 modalities)
              </Typography>
            </Box>
          </Paper>

          <Button
            fullWidth
            variant="contained"
            onClick={handleSimulate}
            disabled={isPending || activeModalities === 0}
            sx={{ py: 1.5 }}
            startIcon={isPending ? <RefreshIcon /> : <SendIcon />}
          >
            {isPending
              ? `Sending to ${sendViaBackend ? 'Backend' : 'ML Service'}…`
              : `Send Signal · ${activeModalities} modalit${activeModalities === 1 ? 'y' : 'ies'}`}
          </Button>
          <FormControlLabel
            sx={{ mt: 1, ml: 0.25 }}
            control={
              <Switch
                size="small"
                checked={sendViaBackend}
                onChange={(e) => setSendViaBackend(e.target.checked)}
              />
            }
            label={
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                {sendViaBackend
                  ? 'Via Backend (persist + alerts)'
                  : 'Direct to ML (no persistence)'}
              </Typography>
            }
          />
          {activeModalities === 0 && (
            <Typography variant="caption" sx={{ color: 'text.secondary', textAlign: 'center', display: 'block', mt: 1 }}>
              Enable at least one modality to send.
            </Typography>
          )}
        </Box>

        {/* Right column: modality controls + last result */}
        <Box sx={{ flex: '1 1 400px', minWidth: 300 }}>
          <ModalityControl
            icon={SpeedIcon}
            label="Metrics"
            description="System metrics: CPU, memory, response time, error rate, request count"
            count={metricsCount}
            setCount={setMetricsCount}
            enabled={metricsEnabled}
            setEnabled={setMetricsEnabled}
            color="hsl(188, 80%, 42%)"
          />
          <ModalityControl
            icon={SpeedIcon}
            label="Logs"
            description="Application log entries with configurable severity levels"
            count={logsCount}
            setCount={setLogsCount}
            enabled={logsEnabled}
            setEnabled={setLogsEnabled}
            color="#f97316"
          />
          <ModalityControl
            icon={SpeedIcon}
            label="Traces"
            description="Distributed trace spans with service name, latency, and status codes"
            count={tracesCount}
            setCount={setTracesCount}
            enabled={tracesEnabled}
            setEnabled={setTracesEnabled}
            color="#a855f7"
          />

          {/* Last result panel */}
          {lastResult && (
            <Paper
              sx={{
                p: 2,
                border: '1px solid',
                borderColor: lastResult.warning ? 'warning.main' : 'success.main',
                backgroundColor: lastResult.warning
                  ? 'rgba(234,179,8,0.05)'
                  : 'rgba(34,197,94,0.05)',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                {lastResult.warning ? (
                  <Warning sx={{ color: 'warning.main' }} />
                ) : (
                  <CheckCircle sx={{ color: 'success.main' }} />
                )}
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {lastResult.warning ? 'Simulation Complete (Mock)' : 'Simulation Complete'}
                </Typography>
                {lastResult.mlResult?._mock && (
                  <Typography
                    variant="caption"
                    sx={{
                      px: 1,
                      py: 0.25,
                      borderRadius: 0.5,
                      backgroundColor: 'rgba(234,179,8,0.15)',
                      color: '#eab308',
                    }}
                  >
                    MOCK
                  </Typography>
                )}
              </Box>
              {lastResult.warning && (
                <Typography variant="caption" sx={{ color: 'warning.main', mb: 1, display: 'block' }}>
                  {lastResult.warning}
                </Typography>
              )}
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                <Box sx={{ flex: '1 1 150px' }}>
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    Hybrid Score
                  </Typography>
                  <ScoreBar
                    score={(lastResult.mlResult?.hybrid_score || lastResult.mlResult?.final_score) ?? 0}
                  />
                </Box>
                <Box sx={{ flex: '1 1 150px', display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                  {[
                    { label: 'MSIF-LSTM', val: lastResult.mlResult?.msif_score ?? 0 },
                    { label: 'PLE-GRU', val: lastResult.mlResult?.ple_score ?? 0 },
                  ].map(({ label, val }) => (
                    <Box key={label} sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                        {label}
                      </Typography>
                      <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                        {val.toFixed(4)}
                      </Typography>
                    </Box>
                  ))}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                      Fusion
                    </Typography>
                    <Typography variant="caption">
                      {lastResult.mlResult?.fusion_method || 'N/A'}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </Paper>
          )}
        </Box>
      </Box>

      {/* History table */}
      <Paper>
        <Box
          sx={{
            px: 2,
            py: 1.5,
            borderBottom: '1px solid',
            borderColor: 'divider',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            Simulation History
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              {history.length} runs
            </Typography>
            <Button
              size="small"
              variant="text"
              sx={{ fontSize: '0.7rem', color: 'text.secondary' }}
              onClick={() => {
                setHistory([]);
                saveHistory([]);
              }}
            >
              Clear
            </Button>
          </Box>
        </Box>
        <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
          {history.length === 0 ? (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                No simulations yet. Send a signal above.
              </Typography>
            </Box>
          ) : (
            <Box>
              {history.map((h) => (
                <Box key={h.id}>
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      flexWrap: 'wrap',
                      gap: 1,
                      px: 2,
                      py: 1,
                      '&:hover': { bgcolor: 'action.hover' },
                      cursor: 'pointer',
                      borderBottom: '1px solid',
                      borderColor: 'divider',
                    }}
                    onClick={() => setExpandedRow(expandedRow === h.id ? null : h.id)}
                  >
                    <Typography variant="caption" sx={{ width: 50, color: 'text.secondary', fontFamily: 'monospace' }}>
                      #{String(h.id).slice(-5)}
                    </Typography>
                    <Typography variant="caption" sx={{ width: 80, color: 'text.secondary', fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
                      {timeAgo(h.timestamp)}
                    </Typography>
                    <Typography
                      variant="caption"
                      sx={{
                        px: 0.75,
                        py: 0.2,
                        borderRadius: 0.5,
                        backgroundColor: h.route === 'backend' ? 'rgba(34,197,94,0.15)' : 'rgba(59,130,246,0.15)',
                        color: h.route === 'backend' ? '#22c55e' : '#3b82f6',
                        fontFamily: 'monospace',
                      }}
                    >
                      {h.route === 'backend' ? 'backend' : 'ml'}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      {h.metricsCount > 0 && (
                        <Typography variant="caption" sx={{ px: 0.5, py: 0.25, borderRadius: 0.5, backgroundColor: 'rgba(59,130,246,0.15)', color: '#3b82f6' }}>
                          M:{h.metricsCount}
                        </Typography>
                      )}
                      {h.logsCount > 0 && (
                        <Typography variant="caption" sx={{ px: 0.5, py: 0.25, borderRadius: 0.5, backgroundColor: 'rgba(249,115,22,0.15)', color: '#f97316' }}>
                          L:{h.logsCount}
                        </Typography>
                      )}
                      {h.tracesCount > 0 && (
                        <Typography variant="caption" sx={{ px: 0.5, py: 0.25, borderRadius: 0.5, backgroundColor: 'rgba(168,85,247,0.15)', color: '#a855f7' }}>
                          T:{h.tracesCount}
                        </Typography>
                      )}
                    </Box>
                    <Box sx={{ width: 80 }}>
                      <SeverityBadge severity={h.severity} />
                    </Box>
                    <Box sx={{ width: 120 }}>
                      {h.hybridScore !== null ? (
                        <ScoreBar score={h.hybridScore} />
                      ) : (
                        <Typography variant="caption" sx={{ color: 'text.secondary' }}>—</Typography>
                      )}
                    </Box>
                    <Typography variant="caption" sx={{ width: 60, color: 'text.secondary', fontFamily: 'monospace' }}>
                      {h.msifScore?.toFixed(4) || '—'}
                    </Typography>
                    <Typography variant="caption" sx={{ width: 60, color: 'text.secondary', fontFamily: 'monospace' }}>
                      {h.pleScore?.toFixed(4) || '—'}
                    </Typography>
                    <Box sx={{ width: 80 }}>
                      {h.finalSeverity ? <SeverityBadge severity={h.finalSeverity} /> : <Typography variant="caption" sx={{ color: 'text.secondary' }}>—</Typography>}
                    </Box>
                    <Typography
                      variant="caption"
                      sx={{
                        px: 1,
                        py: 0.25,
                        borderRadius: 0.5,
                        backgroundColor:
                          h.status === 'completed' ? 'rgba(34,197,94,0.15)' :
                            h.status === 'completed_mock' ? 'rgba(234,179,8,0.15)' :
                              h.status === 'running' ? 'rgba(59,130,246,0.15)' :
                                'rgba(107,114,128,0.15)',
                        color:
                          h.status === 'completed' ? '#22c55e' :
                            h.status === 'completed_mock' ? '#eab308' :
                              h.status === 'running' ? '#3b82f6' :
                                '#6b7280',
                      }}
                    >
                      {h.status}
                    </Typography>
                    <Box sx={{ ml: 'auto' }}>
                      {expandedRow === h.id ? <KeyboardArrowUp /> : <KeyboardArrowDown />}
                    </Box>
                  </Box>

                  {/* Expanded row: raw ML response */}
                  {expandedRow === h.id && h.responsePayload && (
                    <Box
                      sx={{
                        p: 2,
                        bgcolor: 'action.hover',
                        borderBottom: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      <Typography variant="caption" sx={{ fontWeight: 500, color: 'text.secondary', mb: 1, display: 'block' }}>
                        Response Payload
                      </Typography>
                      <Box
                        component="pre"
                        sx={{
                          fontSize: '0.75rem',
                          fontFamily: 'monospace',
                          bgcolor: 'background.paper',
                          p: 1.5,
                          borderRadius: 1,
                          overflow: 'auto',
                          maxHeight: 200,
                          m: 0,
                        }}
                      >
                        {JSON.stringify(JSON.parse(h.responsePayload), null, 2)}
                      </Box>
                      {h.error && (
                        <Typography variant="caption" sx={{ color: 'warning.main', mt: 1, display: 'block' }}>
                          {h.error}
                        </Typography>
                      )}
                    </Box>
                  )}
                </Box>
              ))}
            </Box>
          )}
        </Box>
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
    </Box>
  );
};

export default Simulator;
