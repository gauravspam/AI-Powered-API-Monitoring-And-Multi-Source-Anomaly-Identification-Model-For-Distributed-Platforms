import type { Express } from "express";
import type { Server } from "http";
import { storage } from "./storage";
import { insertSimulationSchema } from "@shared/schema";

export async function registerRoutes(httpServer: Server, app: Express): Promise<Server> {
  
  // --- Simulation routes ---
  app.post("/api/simulate", async (req, res) => {
    try {
      const body = req.body;
      const metricsCount = parseInt(body.metricsCount) || 0;
      const logsCount = parseInt(body.logsCount) || 0;
      const tracesCount = parseInt(body.tracesCount) || 0;
      const severity = body.severity || "MEDIUM";

      // Create simulation record
      const sim = storage.createSimulation({
        timestamp: new Date().toISOString(),
        metricsCount,
        logsCount,
        tracesCount,
        severity,
        status: "running",
      });

      // Build payload for ML service
      const severityToMetrics: Record<string, { cpu_usage: number; memory_usage: number; response_time_ms: number; error_rate: number }> = {
        NORMAL: { cpu_usage: 25, memory_usage: 35, response_time_ms: 120, error_rate: 0.01 },
        LOW:    { cpu_usage: 45, memory_usage: 55, response_time_ms: 350, error_rate: 0.05 },
        MEDIUM: { cpu_usage: 65, memory_usage: 70, response_time_ms: 900, error_rate: 0.15 },
        HIGH:   { cpu_usage: 82, memory_usage: 85, response_time_ms: 2500, error_rate: 0.30 },
        CRITICAL: { cpu_usage: 95, memory_usage: 92, response_time_ms: 5500, error_rate: 0.60 },
      };

      const severityToLogLevel: Record<string, string> = {
        NORMAL: "INFO", LOW: "DEBUG", MEDIUM: "WARN", HIGH: "ERROR", CRITICAL: "FATAL"
      };

      const severityToTraceLatency: Record<string, number> = {
        NORMAL: 80, LOW: 200, MEDIUM: 600, HIGH: 2000, CRITICAL: 6000
      };

      const metricTemplate = severityToMetrics[severity] || severityToMetrics.MEDIUM;
      const logLevel = severityToLogLevel[severity] || "INFO";
      const traceLatency = severityToTraceLatency[severity] || 600;

      const payload: Record<string, unknown> = {};

      if (metricsCount > 0) {
        payload.metrics = {
          ...metricTemplate,
          request_count: 100 + Math.floor(Math.random() * 500),
        };
      }

      if (logsCount > 0) {
        payload.logs = Array.from({ length: Math.min(logsCount, 20) }, (_, i) => ({
          level: logLevel,
          message: `[${severity}] Service event ${i + 1}: anomaly indicator detected`,
          timestamp: new Date(Date.now() - i * 1000).toISOString(),
          service: "api-gateway",
        }));
      }

      if (tracesCount > 0) {
        payload.traces = Array.from({ length: Math.min(tracesCount, 20) }, (_, i) => ({
          traceId: `trace-${Date.now()}-${i}`,
          spanId: `span-${i}`,
          service: "api-gateway",
          operation: "POST /api/ingest",
          latency_ms: traceLatency + Math.floor(Math.random() * 200),
          status: severity === "CRITICAL" || severity === "HIGH" ? "error" : "ok",
          duration: traceLatency,
        }));
      }

      // Forward to ML service
      try {
        const mlUrl = process.env.ML_SERVICE_URL || "http://localhost:9000";
        const mlEndpoint = (metricsCount > 0 || logsCount > 0 || tracesCount > 0)
          ? `${mlUrl}/predict/flexible`
          : `${mlUrl}/predict`;

        const mlResponse = await fetch(mlEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: AbortSignal.timeout(10000),
        });

        if (!mlResponse.ok) {
          throw new Error(`ML service returned ${mlResponse.status}`);
        }

        const mlResult = await mlResponse.json() as Record<string, unknown>;
        const updated = storage.updateSimulation(sim.id, {
          status: "completed",
          responsePayload: JSON.stringify(mlResult),
          hybridScore: (mlResult.hybrid_score || mlResult.final_score) as number,
          msifScore: mlResult.msif_score as number,
          pleScore: mlResult.ple_score as number,
          finalSeverity: mlResult.severity as string,
        });

        res.json({ success: true, simulation: updated, mlResult });
      } catch (mlErr: unknown) {
        const errorMsg = mlErr instanceof Error ? mlErr.message : "ML service unreachable";
        
        // Return mock result when ML service is offline
        const mockScore = { NORMAL: 0.05, LOW: 0.28, MEDIUM: 0.52, HIGH: 0.73, CRITICAL: 0.91 }[severity] || 0.5;
        const mockResult = {
          status: "success",
          hybrid_score: mockScore,
          msif_score: +(mockScore * 0.95).toFixed(4),
          ple_score: +(mockScore * 1.02).toFixed(4),
          severity,
          fusion_method: "rule-based-fallback",
          confidence: 0.6,
          _mock: true,
        };

        const updated = storage.updateSimulation(sim.id, {
          status: "completed_mock",
          responsePayload: JSON.stringify(mockResult),
          hybridScore: mockScore,
          msifScore: mockScore * 0.95,
          pleScore: mockScore * 1.02,
          finalSeverity: severity,
          error: `ML offline (mock): ${errorMsg}`,
        });

        res.json({ success: true, simulation: updated, mlResult: mockResult, warning: `ML service offline — using mock scores. ${errorMsg}` });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      res.status(500).json({ error: msg });
    }
  });

  app.get("/api/simulate/history", async (_req, res) => {
    try {
      const history = storage.getSimulations(50);
      res.json(history);
    } catch (err: unknown) {
      res.status(500).json({ error: "Failed to fetch history" });
    }
  });

  // Proxy routes to backend service (optional — returns mock if backend is down)
  const backendUrl = process.env.BACKEND_URL || "http://localhost:8080";

  async function proxyOrMock(path: string, mockFn: () => unknown): Promise<unknown> {
    try {
      const resp = await fetch(`${backendUrl}${path}`, {
        signal: AbortSignal.timeout(5000),
      });
      if (!resp.ok) throw new Error("Backend error");
      return await resp.json();
    } catch {
      return mockFn();
    }
  }

  app.get("/api/proxy/overview", async (_req, res) => {
    const data = await proxyOrMock("/api/overview", () => ({
      totalServices: 12,
      totalMetrics: 15420,
      totalLogs: 8950,
      totalTraces: 4520,
      totalAnomalies: 23,
      activeAnomalies: 5,
      healthyServices: 10,
      degradedServices: 2,
      _mock: true,
    }));
    res.json(data);
  });

  app.get("/api/proxy/anomalies", async (_req, res) => {
    const data = await proxyOrMock("/api/anomalies/recent?limit=20", () => generateMockAnomalies());
    res.json(data);
  });

  app.get("/api/proxy/alerts", async (_req, res) => {
    const data = await proxyOrMock("/api/alerts?limit=30", () => generateMockAnomalies());
    res.json(data);
  });

  app.get("/api/proxy/logs", async (_req, res) => {
    const data = await proxyOrMock("/api/logs/recent?limit=50", () => generateMockLogs());
    res.json(data);
  });

  app.get("/api/proxy/traces", async (_req, res) => {
    const data = await proxyOrMock("/api/traces/recent?page=0&size=30", () => ({
      content: generateMockTraces(),
      totalElements: 30,
    }));
    res.json(data);
  });

  app.get("/api/proxy/services", async (_req, res) => {
    const data = await proxyOrMock("/api/services", () => generateMockServices());
    res.json(data);
  });

  app.get("/api/proxy/models", async (_req, res) => {
    const data = await proxyOrMock("/api/models", () => generateMockModels());
    res.json(data);
  });

  app.get("/api/proxy/metrics/traffic", async (_req, res) => {
    const data = await proxyOrMock("/api/metrics/traffic?limit=30", () => generateMockTrafficMetrics());
    res.json(data);
  });

  return httpServer;
}

function generateMockAnomalies() {
  const services = ["api-gateway", "payment-service", "user-service", "auth-service", "notification-service"];
  const endpoints = ["/api/users", "/payment/checkout", "/auth/login", "/api/orders", "/api/events"];
  const severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
  const statuses = ["ACTIVE", "ACKNOWLEDGED", "RESOLVED"];

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
    environment: i % 2 === 0 ? "production" : "staging",
    _mock: true,
  }));
}

function generateMockLogs() {
  const levels = ["INFO", "WARN", "ERROR", "DEBUG", "CRITICAL"];
  const services = ["api-gateway", "payment-service", "user-service", "auth-service"];
  return Array.from({ length: 50 }, (_, i) => ({
    id: `log-${Date.now()}-${i}`,
    level: levels[i % 5],
    message: [
      "Request processed successfully",
      "High latency detected on endpoint",
      "Connection timeout to downstream service",
      "Cache miss rate elevated",
      "Database query exceeded threshold",
      "JWT token validation failed",
      "Rate limit exceeded for client",
      "Service health check failed",
    ][i % 8],
    serviceName: services[i % 4],
    timestamp: new Date(Date.now() - i * 45000).toISOString(),
    traceId: `trace-${Math.random().toString(36).substr(2, 9)}`,
    environment: i % 2 === 0 ? "production" : "staging",
    _mock: true,
  }));
}

function generateMockTraces() {
  const services = ["api-gateway", "payment-service", "user-service", "auth-service"];
  const operations = ["GET /api/health", "POST /payment/process", "GET /api/users", "POST /auth/login"];
  return Array.from({ length: 30 }, (_, i) => ({
    id: i + 1,
    traceId: `trace-${Math.random().toString(36).substr(2, 9)}`,
    spanId: `span-${i}`,
    serviceName: services[i % 4],
    operationName: operations[i % 4],
    durationMs: Math.floor(50 + Math.random() * 2000),
    statusCode: i % 5 === 0 ? 500 : i % 7 === 0 ? 429 : 200,
    timestamp: new Date(Date.now() - i * 120000).toISOString(),
    tags: { env: "production", version: "1.0.0" },
    _mock: true,
  }));
}

function generateMockServices() {
  return [
    { id: 1, name: "api-gateway", ownerTeam: "Platform", environment: "production", status: "healthy", avgLatencyMs: 45, errorRate: 0.02, anomalyRate: 0.1, requestPerMin: 1200 },
    { id: 2, name: "payment-service", ownerTeam: "Commerce", environment: "production", status: "degraded", avgLatencyMs: 312, errorRate: 0.08, anomalyRate: 0.4, requestPerMin: 340 },
    { id: 3, name: "user-service", ownerTeam: "Identity", environment: "production", status: "healthy", avgLatencyMs: 67, errorRate: 0.01, anomalyRate: 0.05, requestPerMin: 890 },
    { id: 4, name: "auth-service", ownerTeam: "Identity", environment: "production", status: "healthy", avgLatencyMs: 38, errorRate: 0.005, anomalyRate: 0.02, requestPerMin: 2100 },
    { id: 5, name: "notification-service", ownerTeam: "Comm", environment: "staging", status: "healthy", avgLatencyMs: 95, errorRate: 0.03, anomalyRate: 0.15, requestPerMin: 450 },
    { id: 6, name: "inventory-service", ownerTeam: "Commerce", environment: "production", status: "healthy", avgLatencyMs: 112, errorRate: 0.02, anomalyRate: 0.08, requestPerMin: 220 },
    { id: 7, name: "analytics-service", ownerTeam: "Data", environment: "production", status: "degraded", avgLatencyMs: 890, errorRate: 0.12, anomalyRate: 0.55, requestPerMin: 180 },
    { id: 8, name: "search-service", ownerTeam: "Discovery", environment: "production", status: "healthy", avgLatencyMs: 78, errorRate: 0.01, anomalyRate: 0.06, requestPerMin: 760 },
  ];
}

function generateMockModels() {
  return [
    { id: 1, name: "MSIF-LSTM", version: "1.0.0", type: "LSTM", status: "online", latencyMs: 45, throughputPerSec: 220, accuracy: 94.2, f1Score: 0.921, precision: 0.935, recall: 0.908, lastRetrainAt: "2026-04-08T10:00:00Z" },
    { id: 2, name: "PLE-GRU", version: "1.0.0", type: "GRU", status: "online", latencyMs: 38, throughputPerSec: 285, accuracy: 91.7, f1Score: 0.894, precision: 0.912, recall: 0.877, lastRetrainAt: "2026-04-08T10:00:00Z" },
    { id: 3, name: "Hybrid Ensemble", version: "1.0.0", type: "Ensemble", status: "online", latencyMs: 82, throughputPerSec: 195, accuracy: 96.1, f1Score: 0.948, precision: 0.961, recall: 0.936, lastRetrainAt: "2026-04-08T10:00:00Z" },
  ];
}

function generateMockTrafficMetrics() {
  const now = Date.now();
  return Array.from({ length: 30 }, (_, i) => ({
    timestamp: new Date(now - (29 - i) * 60000).toISOString(),
    requestCount: 800 + Math.floor(Math.random() * 600),
    errorRate: parseFloat((0.01 + Math.random() * 0.08).toFixed(4)),
    avgLatencyMs: Math.floor(50 + Math.random() * 200),
    p99LatencyMs: Math.floor(200 + Math.random() * 800),
  }));
}
