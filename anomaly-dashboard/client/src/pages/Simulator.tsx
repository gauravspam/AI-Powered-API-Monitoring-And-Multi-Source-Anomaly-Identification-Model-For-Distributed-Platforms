import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { Zap, Send, RefreshCw, Activity, FileText, GitBranch, ChevronDown, ChevronUp, AlertTriangle, CheckCircle } from "lucide-react";
import { SeverityBadge, ScoreBar, timeAgo } from "@/components/shared/SeverityBadge";
import { useToast } from "@/hooks/use-toast";
import { Slider } from "@/components/ui/slider";
import { Progress } from "@/components/ui/progress";

type SimHistory = {
  id: number;
  timestamp: string;
  metricsCount: number;
  logsCount: number;
  tracesCount: number;
  severity: string;
  status: string;
  hybridScore: number | null;
  msifScore: number | null;
  pleScore: number | null;
  finalSeverity: string | null;
  responsePayload: string | null;
  error: string | null;
};

type SimResult = {
  success: boolean;
  simulation: SimHistory;
  mlResult: Record<string, unknown>;
  warning?: string;
};

const SEVERITY_OPTIONS = [
  { label: "Normal", value: "NORMAL", score: 0.05, description: "CPU ~25%, Mem ~35%, Latency ~120ms, Error 1%" },
  { label: "Low", value: "LOW", score: 0.28, description: "CPU ~45%, Mem ~55%, Latency ~350ms, Error 5%" },
  { label: "Medium", value: "MEDIUM", score: 0.52, description: "CPU ~65%, Mem ~70%, Latency ~900ms, Error 15%" },
  { label: "High", value: "HIGH", score: 0.73, description: "CPU ~82%, Mem ~85%, Latency ~2.5s, Error 30%" },
  { label: "Critical", value: "CRITICAL", score: 0.91, description: "CPU ~95%, Mem ~92%, Latency ~5.5s, Error 60%" },
];

const SEVERITY_COLORS: Record<string, string> = {
  NORMAL: "#6b7280",
  LOW: "#22c55e",
  MEDIUM: "#eab308",
  HIGH: "#f97316",
  CRITICAL: "#ef4444",
};

function ModalityControl({
  icon: Icon,
  label,
  description,
  count,
  setCount,
  enabled,
  setEnabled,
  color,
  testId,
}: {
  icon: React.ElementType;
  label: string;
  description: string;
  count: number;
  setCount: (v: number) => void;
  enabled: boolean;
  setEnabled: (v: boolean) => void;
  color: string;
  testId: string;
}) {
  return (
    <div className={`rounded-lg border bg-card p-4 space-y-3 transition-all ${enabled ? "border-primary/50" : "border-border opacity-60"}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon size={15} style={{ color }} />
          <span className="text-sm font-semibold text-foreground">{label}</span>
          <span
            className={`text-xs tabular-nums px-1.5 py-0.5 rounded font-mono ${enabled ? "badge-info" : "badge-normal"}`}
          >
            {enabled ? count : 0}
          </span>
        </div>
        <button
          onClick={() => setEnabled(!enabled)}
          className={`text-xs px-2 py-1 rounded transition-colors font-medium ${
            enabled ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
          }`}
          data-testid={`button-toggle-${testId}`}
        >
          {enabled ? "Enabled" : "Disabled"}
        </button>
      </div>
      <p className="text-xs text-muted-foreground">{description}</p>
      {enabled && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Count</span>
            <span className="tabular-nums font-mono">{count}</span>
          </div>
          <Slider
            min={1}
            max={20}
            step={1}
            value={[count]}
            onValueChange={([v]) => setCount(v)}
            className="w-full"
            data-testid={`slider-${testId}-count`}
          />
          <div className="flex justify-between text-[10px] text-muted-foreground">
            <span>1</span>
            <span>20</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default function SimulatorPage() {
  const { toast } = useToast();
  const qc = useQueryClient();

  const [severity, setSeverity] = useState("MEDIUM");
  const [metricsEnabled, setMetricsEnabled] = useState(true);
  const [logsEnabled, setLogsEnabled] = useState(true);
  const [tracesEnabled, setTracesEnabled] = useState(true);
  const [metricsCount, setMetricsCount] = useState(1);
  const [logsCount, setLogsCount] = useState(5);
  const [tracesCount, setTracesCount] = useState(3);
  const [lastResult, setLastResult] = useState<SimResult | null>(null);
  const [expandedRow, setExpandedRow] = useState<number | null>(null);

  const { data: history, isLoading: histLoading } = useQuery<SimHistory[]>({
    queryKey: ["/api/simulate/history"],
    queryFn: () => apiRequest("GET", "/api/simulate/history").then(r => r.json()),
    refetchInterval: 10000,
  });

  const simulate = useMutation({
    mutationFn: async () => {
      const body = {
        metricsCount: metricsEnabled ? metricsCount : 0,
        logsCount: logsEnabled ? logsCount : 0,
        tracesCount: tracesEnabled ? tracesCount : 0,
        severity,
      };
      const res = await apiRequest("POST", "/api/simulate", body);
      return res.json() as Promise<SimResult>;
    },
    onSuccess: (data) => {
      setLastResult(data);
      qc.invalidateQueries({ queryKey: ["/api/simulate/history"] });
      if (data.warning) {
        toast({ title: "Simulation Complete (Mock)", description: data.warning, variant: "default" });
      } else {
        toast({ title: "Simulation Complete", description: `ML returned severity: ${data.mlResult?.severity}` });
      }
    },
    onError: (e: Error) => {
      toast({ title: "Simulation Failed", description: e.message, variant: "destructive" });
    },
  });

  const activeModalities = [metricsEnabled, logsEnabled, tracesEnabled].filter(Boolean).length;
  const selectedSev = SEVERITY_OPTIONS.find(s => s.value === severity)!;

  return (
    <div className="space-y-5">
      {/* Intro */}
      <div className="rounded-lg border border-border bg-card p-4 flex items-start gap-3">
        <Zap size={16} className="text-primary mt-0.5 shrink-0" />
        <div>
          <div className="text-sm font-semibold text-foreground">Signal Simulator</div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Send synthetic telemetry signals (metrics, logs, traces) to the ML service via <span className="font-mono text-primary">POST /predict/flexible</span>.
            The backend forwards to OpenSearch and ML models for anomaly scoring. Configure modalities and severity level below.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* Left: Config panel */}
        <div className="lg:col-span-2 space-y-4">
          {/* Severity selector */}
          <div className="rounded-lg border border-border bg-card p-4 space-y-3">
            <div className="text-sm font-semibold text-foreground">Severity Level</div>
            <div className="space-y-1.5">
              {SEVERITY_OPTIONS.map(opt => (
                <button
                  key={opt.value}
                  onClick={() => setSeverity(opt.value)}
                  className={`w-full text-left rounded-md px-3 py-2.5 transition-all ${
                    severity === opt.value
                      ? "bg-muted border border-primary/50"
                      : "hover:bg-muted/60 border border-transparent"
                  }`}
                  data-testid={`button-severity-${opt.value.toLowerCase()}`}
                >
                  <div className="flex items-center justify-between">
                    <span
                      className="text-sm font-medium"
                      style={{ color: severity === opt.value ? SEVERITY_COLORS[opt.value] : undefined }}
                    >
                      {opt.label}
                    </span>
                    <span className="text-xs tabular-nums text-muted-foreground">{opt.score.toFixed(2)}</span>
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-0.5 leading-tight">{opt.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Expected score preview */}
          <div className="rounded-lg border border-border bg-card p-4 space-y-3">
            <div className="text-sm font-semibold text-foreground">Expected Score</div>
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Hybrid Score</span>
                <span className="tabular-nums" style={{ color: SEVERITY_COLORS[severity] }}>~{selectedSev.score.toFixed(2)}</span>
              </div>
              <div className="h-2 rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${selectedSev.score * 100}%`, background: SEVERITY_COLORS[severity] }}
                />
              </div>
              <div className="flex items-center gap-1.5 text-xs">
                <span className="text-muted-foreground">Confidence:</span>
                <span className="tabular-nums text-foreground">{(activeModalities / 3).toFixed(2)}</span>
                <span className="text-muted-foreground">({activeModalities}/3 modalities)</span>
              </div>
            </div>
          </div>

          {/* Send button */}
          <button
            onClick={() => simulate.mutate()}
            disabled={simulate.isPending || activeModalities === 0}
            className="w-full flex items-center justify-center gap-2 py-3 rounded-lg bg-primary text-primary-foreground font-semibold text-sm hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="button-send-simulation"
          >
            {simulate.isPending ? (
              <>
                <RefreshCw size={15} className="animate-spin" />
                Sending to ML Service…
              </>
            ) : (
              <>
                <Send size={15} />
                Send Signal · {activeModalities} modalit{activeModalities === 1 ? "y" : "ies"}
              </>
            )}
          </button>
          {activeModalities === 0 && (
            <p className="text-xs text-center text-muted-foreground">Enable at least one modality to send.</p>
          )}
        </div>

        {/* Right: Modality controls + result */}
        <div className="lg:col-span-3 space-y-4">
          {/* Modality controls */}
          <ModalityControl
            icon={Activity}
            label="Metrics"
            description="System metrics: CPU, memory, response time, error rate, request count"
            count={metricsCount}
            setCount={setMetricsCount}
            enabled={metricsEnabled}
            setEnabled={setMetricsEnabled}
            color="hsl(188, 80%, 42%)"
            testId="metrics"
          />
          <ModalityControl
            icon={FileText}
            label="Logs"
            description="Application log entries with configurable severity levels"
            count={logsCount}
            setCount={setLogsCount}
            enabled={logsEnabled}
            setEnabled={setLogsEnabled}
            color="#f97316"
            testId="logs"
          />
          <ModalityControl
            icon={GitBranch}
            label="Traces"
            description="Distributed trace spans with service name, latency, and status codes"
            count={tracesCount}
            setCount={setTracesCount}
            enabled={tracesEnabled}
            setEnabled={setTracesEnabled}
            color="#a855f7"
            testId="traces"
          />

          {/* Last result */}
          {lastResult && (
            <div className={`rounded-lg border p-4 space-y-3 ${
              lastResult.warning ? "border-yellow-500/30 bg-yellow-500/5" : "border-green-500/30 bg-green-500/5"
            }`}>
              <div className="flex items-center gap-2">
                {lastResult.warning
                  ? <AlertTriangle size={14} className="text-yellow-400" />
                  : <CheckCircle size={14} className="text-green-400" />
                }
                <span className="text-sm font-semibold text-foreground">
                  {lastResult.warning ? "Simulation Complete (Mock)" : "Simulation Complete"}
                </span>
                {lastResult.mlResult?._mock && (
                  <span className="text-xs badge-medium rounded px-1.5 py-0.5">MOCK</span>
                )}
              </div>

              {lastResult.warning && (
                <p className="text-xs text-yellow-400/80">{lastResult.warning}</p>
              )}

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Hybrid Score</span>
                    <span className="tabular-nums font-mono text-foreground">{lastResult.mlResult?.hybrid_score?.toFixed(4) || lastResult.mlResult?.final_score?.toFixed(4)}</span>
                  </div>
                  <ScoreBar score={((lastResult.mlResult?.hybrid_score || lastResult.mlResult?.final_score) as number) || 0} />
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">MSIF-LSTM</span>
                    <span className="tabular-nums font-mono text-foreground">{(lastResult.mlResult?.msif_score as number)?.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">PLE-GRU</span>
                    <span className="tabular-nums font-mono text-foreground">{(lastResult.mlResult?.ple_score as number)?.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Fusion</span>
                    <span className="text-foreground">{lastResult.mlResult?.fusion_method as string}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 pt-1 border-t border-border">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Severity:</span>
                  <SeverityBadge severity={lastResult.mlResult?.severity as string || lastResult.simulation.finalSeverity || "UNKNOWN"} />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Confidence:</span>
                  <span className="text-xs tabular-nums text-foreground">{((lastResult.mlResult?.confidence as number) || 0).toFixed(2)}</span>
                </div>
                {(lastResult.mlResult?.modalities_present as number) !== undefined && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">Modalities:</span>
                    <span className="text-xs tabular-nums text-foreground">{lastResult.mlResult.modalities_present as number}/3</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Simulation history */}
      <div className="rounded-lg border border-border bg-card">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h2 className="text-sm font-semibold text-foreground">Simulation History</h2>
          <span className="text-xs text-muted-foreground tabular-nums">{(history || []).length} runs</span>
        </div>

        {histLoading ? (
          <div className="p-4 space-y-2">
            {[1, 2, 3].map(i => <div key={i} className="h-10 animate-pulse bg-muted rounded" />)}
          </div>
        ) : (history || []).length === 0 ? (
          <div className="p-8 text-center text-sm text-muted-foreground">No simulations yet. Send a signal above.</div>
        ) : (
          <div className="overflow-x-auto sticky-thead">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-muted-foreground border-b border-border">
                  <th className="text-left px-4 py-2.5 font-medium">#</th>
                  <th className="text-left px-4 py-2.5 font-medium">Time</th>
                  <th className="text-left px-4 py-2.5 font-medium">Modalities</th>
                  <th className="text-left px-4 py-2.5 font-medium">Severity</th>
                  <th className="text-left px-4 py-2.5 font-medium">Hybrid Score</th>
                  <th className="text-left px-4 py-2.5 font-medium">MSIF</th>
                  <th className="text-left px-4 py-2.5 font-medium">PLE</th>
                  <th className="text-left px-4 py-2.5 font-medium">Result</th>
                  <th className="text-left px-4 py-2.5 font-medium">Status</th>
                  <th className="text-left px-4 py-2.5 font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {(history || []).map((h) => (
                  <>
                    <tr
                      key={h.id}
                      className="hover:bg-muted/40 transition-colors cursor-pointer"
                      onClick={() => setExpandedRow(expandedRow === h.id ? null : h.id)}
                      data-testid={`row-sim-${h.id}`}
                    >
                      <td className="px-4 py-2.5 text-xs text-muted-foreground tabular-nums">#{h.id}</td>
                      <td className="px-4 py-2.5 text-xs text-muted-foreground tabular-nums whitespace-nowrap">{timeAgo(h.timestamp)}</td>
                      <td className="px-4 py-2.5 text-xs">
                        <div className="flex items-center gap-1">
                          {h.metricsCount > 0 && <span title="Metrics" className="badge-info rounded px-1 py-0.5">M:{h.metricsCount}</span>}
                          {h.logsCount > 0 && <span title="Logs" className="badge-high rounded px-1 py-0.5">L:{h.logsCount}</span>}
                          {h.tracesCount > 0 && <span title="Traces" className="badge-medium rounded px-1 py-0.5" style={{ background: "rgba(168,85,247,0.15)", color: "#a855f7", border: "1px solid rgba(168,85,247,0.3)" }}>T:{h.tracesCount}</span>}
                        </div>
                      </td>
                      <td className="px-4 py-2.5"><SeverityBadge severity={h.severity} /></td>
                      <td className="px-4 py-2.5 w-32">
                        {h.hybridScore !== null ? <ScoreBar score={h.hybridScore} /> : <span className="text-muted-foreground text-xs">—</span>}
                      </td>
                      <td className="px-4 py-2.5 text-xs tabular-nums text-muted-foreground">{h.msifScore?.toFixed(4) || "—"}</td>
                      <td className="px-4 py-2.5 text-xs tabular-nums text-muted-foreground">{h.pleScore?.toFixed(4) || "—"}</td>
                      <td className="px-4 py-2.5">
                        {h.finalSeverity ? <SeverityBadge severity={h.finalSeverity} /> : <span className="text-xs text-muted-foreground">—</span>}
                      </td>
                      <td className="px-4 py-2.5">
                        <span className={`text-xs rounded px-1.5 py-0.5 ${
                          h.status === "completed" ? "badge-low" :
                          h.status === "completed_mock" ? "badge-medium" :
                          h.status === "running" ? "badge-info" : "badge-normal"
                        }`}>
                          {h.status}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-muted-foreground">
                        {expandedRow === h.id ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                      </td>
                    </tr>
                    {expandedRow === h.id && h.responsePayload && (
                      <tr key={`${h.id}-exp`} className="bg-muted/20">
                        <td colSpan={10} className="px-4 py-3">
                          <div className="space-y-1">
                            <div className="text-xs font-medium text-muted-foreground mb-2">ML Service Response</div>
                            <pre className="text-xs font-mono text-foreground bg-muted rounded p-3 overflow-x-auto max-h-48">
                              {JSON.stringify(JSON.parse(h.responsePayload), null, 2)}
                            </pre>
                            {h.error && (
                              <p className="text-xs text-yellow-400 mt-1">{h.error}</p>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
