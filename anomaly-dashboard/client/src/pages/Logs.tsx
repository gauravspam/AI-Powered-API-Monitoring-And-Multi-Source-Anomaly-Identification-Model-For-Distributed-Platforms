import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useState, useRef, useEffect } from "react";
import { Search, RefreshCw, ArrowDown } from "lucide-react";
import { SeverityBadge, LoadingRows, EmptyState, timeAgo } from "@/components/shared/SeverityBadge";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";

type Log = {
  id: string;
  level: string;
  message: string;
  serviceName: string;
  timestamp: string;
  traceId?: string;
  environment?: string;
};

const LEVEL_ORDER = ["CRITICAL", "FATAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG"];

export default function LogsPage() {
  const [search, setSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState("all");
  const [autoScroll, setAutoScroll] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: logs, isLoading, refetch, isFetching } = useQuery<Log[]>({
    queryKey: ["/api/proxy/logs"],
    queryFn: () => apiRequest("GET", "/api/proxy/logs").then(r => r.json()),
    refetchInterval: autoScroll ? 5000 : false,
  });

  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, autoScroll]);

  const filtered = (Array.isArray(logs) ? logs : []).filter(l => {
    const matchLevel = levelFilter === "all" || l.level?.toUpperCase() === levelFilter;
    const matchSearch = !search ||
      l.message?.toLowerCase().includes(search.toLowerCase()) ||
      l.serviceName?.toLowerCase().includes(search.toLowerCase()) ||
      l.traceId?.toLowerCase().includes(search.toLowerCase());
    return matchLevel && matchSearch;
  });

  const levelCounts = (Array.isArray(logs) ? logs : []).reduce((acc: Record<string, number>, l) => {
    const lvl = (l.level || "INFO").toUpperCase();
    acc[lvl] = (acc[lvl] || 0) + 1;
    return acc;
  }, {});

  const levelColor: Record<string, string> = {
    CRITICAL: "text-red-400", FATAL: "text-red-400",
    ERROR: "text-red-400", WARN: "text-orange-400",
    WARNING: "text-orange-400", INFO: "text-blue-400",
    DEBUG: "text-muted-foreground",
  };

  return (
    <div className="space-y-4">
      {/* Level summary */}
      <div className="flex items-center gap-2 flex-wrap">
        {LEVEL_ORDER.slice(0, 6).map(lvl => (
          <div key={lvl} className="flex items-center gap-1.5 rounded border border-border bg-card px-2.5 py-1.5">
            <span className={`text-xs font-medium ${levelColor[lvl]}`}>{lvl}</span>
            <span className="text-xs tabular-nums text-muted-foreground">{levelCounts[lvl] || 0}</span>
          </div>
        ))}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search messages, services, trace IDs…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-7 h-8 text-sm bg-card font-mono"
            data-testid="input-log-search"
          />
        </div>
        <div className="flex gap-1">
          {["all", "ERROR", "WARN", "INFO", "DEBUG"].map(lvl => (
            <button
              key={lvl}
              onClick={() => setLevelFilter(lvl)}
              className={`px-2.5 py-1 text-xs rounded font-medium transition-colors ${
                levelFilter === lvl ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:text-foreground"
              }`}
              data-testid={`button-level-${lvl}`}
            >
              {lvl === "all" ? "All" : lvl}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 ml-auto">
          <span className="text-xs text-muted-foreground">Live tail</span>
          <Switch
            checked={autoScroll}
            onCheckedChange={setAutoScroll}
            data-testid="switch-autoscroll"
          />
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            data-testid="button-refresh-logs"
          >
            <RefreshCw size={12} className={isFetching ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* Log stream */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="bg-muted/30 px-4 py-2 flex items-center justify-between border-b border-border">
          <span className="text-xs text-muted-foreground font-mono">
            {filtered.length} entries {search || levelFilter !== "all" ? "(filtered)" : ""}
          </span>
          {autoScroll && (
            <span className="flex items-center gap-1 text-xs text-primary">
              <span className="w-1.5 h-1.5 rounded-full bg-primary status-dot-live" />
              Streaming
            </span>
          )}
        </div>

        <div className="overflow-x-auto sticky-thead" style={{ maxHeight: "calc(100dvh - 340px)", overflowY: "auto" }}>
          <table className="w-full text-xs font-mono">
            <thead>
              <tr className="text-muted-foreground">
                <th className="text-left px-4 py-2 font-medium w-32">Time</th>
                <th className="text-left px-4 py-2 font-medium w-20">Level</th>
                <th className="text-left px-4 py-2 font-medium w-28">Service</th>
                <th className="text-left px-4 py-2 font-medium">Message</th>
                <th className="text-left px-4 py-2 font-medium w-32">Trace ID</th>
                <th className="text-left px-4 py-2 font-medium w-20">Env</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <LoadingRows cols={6} rows={8} />
              ) : filtered.length === 0 ? (
                <tr><td colSpan={6}><EmptyState message="No log entries found" /></td></tr>
              ) : (
                filtered.map((l, i) => (
                  <tr
                    key={`${l.id}-${i}`}
                    className="border-t border-border/50 hover:bg-muted/20 transition-colors"
                    data-testid={`row-log-${i}`}
                  >
                    <td className="px-4 py-1.5 text-muted-foreground tabular-nums whitespace-nowrap">
                      {new Date(l.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="px-4 py-1.5">
                      <span className={`font-semibold ${levelColor[(l.level || "INFO").toUpperCase()] || "text-muted-foreground"}`}>
                        {(l.level || "INFO").toUpperCase().padEnd(5)}
                      </span>
                    </td>
                    <td className="px-4 py-1.5 text-primary truncate max-w-[120px]">{l.serviceName}</td>
                    <td className="px-4 py-1.5 text-foreground max-w-[400px] truncate" title={l.message}>
                      {l.message}
                    </td>
                    <td className="px-4 py-1.5 text-muted-foreground truncate max-w-[120px]">{l.traceId || "—"}</td>
                    <td className="px-4 py-1.5">
                      <SeverityBadge severity={l.environment || "unknown"} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          <div ref={bottomRef} />
        </div>
      </div>

      {autoScroll && (
        <div className="flex justify-center">
          <button
            onClick={() => bottomRef.current?.scrollIntoView({ behavior: "smooth" })}
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowDown size={12} /> Jump to bottom
          </button>
        </div>
      )}
    </div>
  );
}
