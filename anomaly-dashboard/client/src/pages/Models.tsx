import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from "recharts";
import { StatusDot, EmptyState } from "@/components/shared/SeverityBadge";

type Model = {
  id: number;
  name: string;
  version: string;
  type: string;
  status: string;
  latencyMs: number;
  throughputPerSec: number;
  accuracy: number;
  f1Score: number;
  precision: number;
  recall: number;
  lastRetrainAt: string;
};

const MODEL_COLORS: Record<string, string> = {
  "MSIF-LSTM": "hsl(188, 80%, 42%)",
  "PLE-GRU": "#f97316",
  "Hybrid Ensemble": "#a855f7",
};

export default function ModelsPage() {
  const { data: models, isLoading } = useQuery<Model[]>({
    queryKey: ["/api/proxy/models"],
    queryFn: () => apiRequest("GET", "/api/proxy/models").then(r => r.json()),
    refetchInterval: 60000,
  });

  const modelList = Array.isArray(models) ? models : [];

  // Performance comparison data
  const comparisonData = [
    { metric: "Accuracy", ...Object.fromEntries(modelList.map(m => [m.name, m.accuracy])) },
    { metric: "F1 Score", ...Object.fromEntries(modelList.map(m => [m.name, +(m.f1Score * 100).toFixed(1)])) },
    { metric: "Precision", ...Object.fromEntries(modelList.map(m => [m.name, +(m.precision * 100).toFixed(1)])) },
    { metric: "Recall", ...Object.fromEntries(modelList.map(m => [m.name, +(m.recall * 100).toFixed(1)])) },
  ];

  // Radar data for each model
  const radarData = [
    { axis: "Accuracy", ...Object.fromEntries(modelList.map(m => [m.name, m.accuracy])) },
    { axis: "F1", ...Object.fromEntries(modelList.map(m => [m.name, +(m.f1Score * 100).toFixed(1)])) },
    { axis: "Precision", ...Object.fromEntries(modelList.map(m => [m.name, +(m.precision * 100).toFixed(1)])) },
    { axis: "Recall", ...Object.fromEntries(modelList.map(m => [m.name, +(m.recall * 100).toFixed(1)])) },
    { axis: "Throughput", ...Object.fromEntries(modelList.map(m => [m.name, Math.min(m.throughputPerSec / 3, 100)])) },
    { axis: "Speed", ...Object.fromEntries(modelList.map(m => [m.name, Math.min(100 - m.latencyMs / 1.5, 100)])) },
  ];

  // Latency/throughput data
  const perfData = modelList.map(m => ({
    name: m.name,
    latency: m.latencyMs,
    throughput: m.throughputPerSec,
  }));

  const CustomTooltip = ({ active, payload, label }: Record<string, unknown>) => {
    if (active && Array.isArray(payload) && payload.length) {
      return (
        <div className="rounded border border-border bg-card p-3 text-xs shadow">
          <p className="text-muted-foreground mb-1 font-medium">{label as string}</p>
          {(payload as Array<{ name: string; value: number; color: string }>).map(p => (
            <p key={p.name} style={{ color: p.color }} className="tabular-nums">
              {p.name}: {typeof p.value === "number" ? p.value.toFixed(1) : p.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="rounded-lg border border-border bg-card p-5 animate-pulse h-32" />
        ))}
      </div>
    );
  }

  if (!modelList.length) return <EmptyState message="No model data available" />;

  return (
    <div className="space-y-5">
      {/* Model cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {modelList.map(m => (
          <div
            key={m.id}
            className="rounded-lg border border-border bg-card p-4 space-y-3"
            data-testid={`card-model-${m.id}`}
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold text-sm text-foreground">{m.name}</div>
                <div className="text-xs text-muted-foreground">v{m.version} · {m.type}</div>
              </div>
              <div className="flex items-center gap-1.5">
                <StatusDot status={m.status} />
                <span className="text-xs capitalize text-muted-foreground">{m.status}</span>
              </div>
            </div>

            {/* Metrics grid */}
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: "Accuracy", value: `${m.accuracy.toFixed(1)}%` },
                { label: "F1 Score", value: m.f1Score.toFixed(3) },
                { label: "Precision", value: m.precision.toFixed(3) },
                { label: "Recall", value: m.recall.toFixed(3) },
              ].map(({ label, value }) => (
                <div key={label} className="rounded bg-muted/50 px-3 py-2">
                  <div className="text-[10px] text-muted-foreground uppercase tracking-wide">{label}</div>
                  <div className="text-sm font-semibold tabular-nums text-foreground mt-0.5">{value}</div>
                </div>
              ))}
            </div>

            <div className="flex justify-between text-xs text-muted-foreground pt-1 border-t border-border">
              <span>P50 latency: <span className="text-foreground tabular-nums">{m.latencyMs}ms</span></span>
              <span>Throughput: <span className="text-foreground tabular-nums">{m.throughputPerSec}/s</span></span>
            </div>

            <div className="text-[10px] text-muted-foreground">
              Last retrained: {new Date(m.lastRetrainAt).toLocaleDateString()}
            </div>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Radar comparison */}
        <div className="rounded-lg border border-border bg-card p-4">
          <h2 className="text-sm font-semibold text-foreground mb-3">Performance Radar</h2>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData} margin={{ top: 8, right: 16, bottom: 8, left: 16 }}>
              <PolarGrid stroke="hsl(var(--border))" />
              <PolarAngleAxis dataKey="axis" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
              {modelList.map(m => (
                <Radar
                  key={m.name}
                  name={m.name}
                  dataKey={m.name}
                  stroke={MODEL_COLORS[m.name] || "#6b7280"}
                  fill={MODEL_COLORS[m.name] || "#6b7280"}
                  fillOpacity={0.1}
                  strokeWidth={1.5}
                />
              ))}
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Bar comparison */}
        <div className="rounded-lg border border-border bg-card p-4">
          <h2 className="text-sm font-semibold text-foreground mb-3">Metrics Comparison</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={comparisonData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis dataKey="metric" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} domain={[80, 100]} width={32} />
              <Tooltip content={<CustomTooltip />} />
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
              {modelList.map(m => (
                <Bar key={m.name} dataKey={m.name} fill={MODEL_COLORS[m.name] || "#6b7280"} radius={[3, 3, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Latency vs throughput */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="text-sm font-semibold text-foreground mb-3">Latency vs Throughput</h2>
        <div className="grid grid-cols-3 gap-4">
          {perfData.map(p => (
            <div key={p.name} className="rounded-lg bg-muted/30 p-4 space-y-3">
              <div
                className="text-sm font-semibold"
                style={{ color: MODEL_COLORS[p.name] || "#6b7280" }}
              >
                {p.name}
              </div>
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">Latency</span>
                    <span className="tabular-nums text-foreground">{p.latency}ms</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${Math.min(p.latency / 1.5, 100)}%`, background: MODEL_COLORS[p.name] || "#6b7280", opacity: 0.7 }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">Throughput</span>
                    <span className="tabular-nums text-foreground">{p.throughput}/s</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${Math.min(p.throughput / 3, 100)}%`, background: MODEL_COLORS[p.name] || "#6b7280" }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Architecture notes */}
      <div className="rounded-lg border border-border bg-card p-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div className="space-y-1">
          <div className="font-semibold text-foreground" style={{ color: MODEL_COLORS["MSIF-LSTM"] }}>MSIF-LSTM</div>
          <div className="text-muted-foreground">Multi-Scale Isolation Forest + LSTM</div>
          <div className="text-muted-foreground">Window: 60 timesteps · 5 features</div>
          <div className="text-muted-foreground">Embedding dim: 3 · Hidden: 64</div>
          <div className="text-muted-foreground">MSIF weight: 0.60 in ensemble</div>
        </div>
        <div className="space-y-1">
          <div className="font-semibold text-foreground" style={{ color: MODEL_COLORS["PLE-GRU"] }}>PLE-GRU</div>
          <div className="text-muted-foreground">Probabilistic Label Enhancement + GRU</div>
          <div className="text-muted-foreground">Window: 1440 timesteps · 7 features</div>
          <div className="text-muted-foreground">Experts: 4 · Hidden: 128</div>
          <div className="text-muted-foreground">PLE weight: 0.40 in ensemble</div>
        </div>
        <div className="space-y-1">
          <div className="font-semibold text-foreground" style={{ color: MODEL_COLORS["Hybrid Ensemble"] }}>Hybrid Ensemble</div>
          <div className="text-muted-foreground">Weighted combination of MSIF-LSTM + PLE-GRU</div>
          <div className="text-muted-foreground">Fusion: weighted_ensemble / rule_based_fallback</div>
          <div className="text-muted-foreground">Threshold: 0.70</div>
          <div className="text-muted-foreground">Confidence scaled by modality count</div>
        </div>
      </div>
    </div>
  );
}
