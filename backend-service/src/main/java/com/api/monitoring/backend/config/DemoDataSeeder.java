package com.api.monitoring.backend.config;

import com.api.monitoring.backend.dto.LogDTO;
import com.api.monitoring.backend.model.AnomalyRecord;
import com.api.monitoring.backend.model.MetricRecord;
import com.api.monitoring.backend.model.TraceRecord;
import com.api.monitoring.backend.repository.AnomalyRepository;
import com.api.monitoring.backend.repository.MetricRepository;
import com.api.monitoring.backend.repository.TraceRepository;
import com.api.monitoring.backend.service.OpenSearchLogService;
import java.time.Instant;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Component;

@Component
@Slf4j
public class DemoDataSeeder implements CommandLineRunner {

    private static final List<ServiceProfile> SERVICE_PROFILES = List.of(
        new ServiceProfile("api-gateway", "/api/gateway/route", "POST /api/gateway/route", "Platform", 65, 2200, 0.010),
        new ServiceProfile("payment-service", "/payment/checkout", "POST /payment/checkout", "Commerce", 220, 620, 0.018),
        new ServiceProfile("user-service", "/api/users", "GET /api/users", "Identity", 95, 1300, 0.008),
        new ServiceProfile("auth-service", "/auth/login", "POST /auth/login", "Identity", 80, 1700, 0.012),
        new ServiceProfile("notification-service", "/api/events", "POST /api/events", "Communications", 130, 900, 0.010),
        new ServiceProfile("order-service", "/api/orders", "GET /api/orders", "Commerce", 170, 780, 0.015)
    );

    private static final Map<String, String> SEVERITY_BY_STATUS = Map.of(
        "CRITICAL", "CRITICAL",
        "ERROR", "HIGH",
        "WARN", "MEDIUM",
        "INFO", "LOW",
        "DEBUG", "LOW"
    );

    private static final int METRIC_POINTS_PER_SERVICE = 36;
    private static final int TRACE_TARGET = 180;
    private static final int ANOMALY_TARGET = 60;
    private static final int LOG_TARGET = 220;

    private final MetricRepository metricRepository;
    private final TraceRepository traceRepository;
    private final AnomalyRepository anomalyRepository;
    private final OpenSearchLogService openSearchLogService;
    private final Random random = new Random(42);
    private final List<SeedTraceRef> seedTraces = new ArrayList<>();
    private final Map<String, String> anomalySeverityByTrace = new HashMap<>();

    @Value("${app.seed-demo-data:true}")
    private boolean seedEnabled;

    public DemoDataSeeder(
            MetricRepository metricRepository,
            TraceRepository traceRepository,
            AnomalyRepository anomalyRepository,
            OpenSearchLogService openSearchLogService) {
        this.metricRepository = metricRepository;
        this.traceRepository = traceRepository;
        this.anomalyRepository = anomalyRepository;
        this.openSearchLogService = openSearchLogService;
    }

    @Override
    public void run(String... args) {
        if (!seedEnabled) {
            log.info("Demo data seeding disabled (app.seed-demo-data=false)");
            return;
        }

        seedMetrics();
        seedTraces();
        seedAnomalies();
        seedLogs();
    }

    private void seedMetrics() {
        long existing = metricRepository.count();
        if (existing >= 120) {
            log.info("Demo metrics already present ({} records), skipping seed", existing);
            return;
        }

        LocalDateTime now = LocalDateTime.now();

        int saved = 0;
        int apiLogId = 1;
        for (ServiceProfile profile : SERVICE_PROFILES) {
            for (int i = 0; i < METRIC_POINTS_PER_SERVICE; i++) {
                LocalDateTime ts = now.minusMinutes(i);
                boolean incident = isIncidentWindow(profile.serviceName(), i);
                double wave = 1.0 + (Math.sin(i / 4.0) * 0.10);
                double latencyMultiplier = incident ? 2.8 : 1.0;

                long responseMs = Math.max(20L,
                    Math.round(profile.baseLatencyMs() * wave * latencyMultiplier + jitter(18.0)));
                int requestCount = Math.max(40,
                    (int) Math.round(profile.baseRpm() * wave + jitter(95.0)));
                double errorRate = clamp(profile.baseErrorRate() + (incident ? 0.09 : 0.0) + jitter(0.003), 0.001, 0.45);
                double cpu = clamp(35 + (responseMs / 18.0) + jitter(4.0), 15, 98);
                double memory = clamp(40 + (requestCount / 110.0) + jitter(3.5), 20, 98);

                MetricRecord metric = new MetricRecord();
                metric.setApiLogId((long) apiLogId++);
                metric.setServiceName(profile.serviceName());
                metric.setEndpoint(profile.endpoint());
                metric.setEnvironment("production");
                metric.setCpuUsagePercent(cpu);
                metric.setMemoryUsagePercent(memory);
                metric.setResponseTimeMs(responseMs);
                metric.setRequestCount(requestCount);
                metric.setErrorRate(errorRate);
                metric.setDiskIoBytes(Math.max(120000L, Math.round(requestCount * 780L + jitter(50000.0))));
                metric.setNetworkIoBytes(Math.max(250000L, Math.round(requestCount * 1400L + jitter(90000.0))));
                metric.setMetricTimestamp(ts);
                metric.setCreatedAt(ts);
                metricRepository.save(metric);
                saved++;
            }
        }

        log.info("Seeded {} demo metrics", saved);
    }

    private void seedTraces() {
        long existing = traceRepository.count();
        if (existing >= 120) {
            log.info("Demo traces already present ({} records), skipping seed", existing);
            hydrateSeedTracesFromDb();
            return;
        }

        LocalDateTime now = LocalDateTime.now();

        for (int i = 0; i < TRACE_TARGET; i++) {
            ServiceProfile profile = SERVICE_PROFILES.get(i % SERVICE_PROFILES.size());
            boolean incident = isIncidentWindow(profile.serviceName(), i % METRIC_POINTS_PER_SERVICE);
            int statusCode = incident
                ? ((i % 3 == 0) ? 503 : (i % 2 == 0 ? 500 : 429))
                : ((i % 17 == 0) ? 404 : 200);

            long duration = Math.max(25L,
                Math.round(profile.baseLatencyMs() * (incident ? 3.0 : 1.0) + jitter(45.0)));
            LocalDateTime ts = now.minusSeconds(i * 35L);
            String traceId = "seed-" + profile.serviceName() + "-" + (TRACE_TARGET - i);
            String spanId = "seed-span-" + (TRACE_TARGET - i);

            TraceRecord trace = TraceRecord.builder()
                .traceId(traceId)
                .spanId(spanId)
                .parentSpanId(i > 0 ? "seed-span-" + (TRACE_TARGET - (i - 1)) : null)
                .serviceName(profile.serviceName())
                .operationName(profile.operation())
                .startTime(ts)
                .duration(duration)
                .statusCode(statusCode)
                .isError(statusCode >= 400)
                .errorMessage(statusCode >= 500 ? "Upstream dependency timeout" : (statusCode >= 400 ? "Client request rejected" : null))
                .createdAt(ts)
                .tags(Map.of(
                    "env", "production",
                    "team", profile.team(),
                    "endpoint", profile.endpoint(),
                    "release", statusCode >= 500 ? "2026.04.2-hotfix" : "2026.04.2"
                ))
                .build();

            traceRepository.save(trace);
            seedTraces.add(new SeedTraceRef(traceId, profile.serviceName(), profile.endpoint(), ts, statusCode, duration));
        }

        log.info("Seeded {} demo traces", TRACE_TARGET);
    }

    private void seedAnomalies() {
        long existing = anomalyRepository.count();
        if (existing >= 45) {
            log.info("Demo anomalies already present ({} records), skipping seed", existing);
            return;
        }

        if (seedTraces.isEmpty()) {
            hydrateSeedTracesFromDb();
        }
        if (seedTraces.isEmpty()) {
            log.warn("No traces available; skipping anomaly seed to preserve relation consistency");
            return;
        }

        int saved = 0;
        for (int i = 0; i < Math.min(ANOMALY_TARGET, seedTraces.size()); i++) {
            SeedTraceRef ref = seedTraces.get(i);
            double severityScore = scoreFromTrace(ref);
            String severity = severityFromScore(severityScore);
            String status = (i % 5 == 0) ? "RESOLVED" : ((i % 3 == 0) ? "ACKNOWLEDGED" : "ACTIVE");

            double msif = clamp(severityScore - 0.03 + jitter(0.01), 0.01, 0.99);
            double ple = clamp(severityScore - 0.01 + jitter(0.01), 0.01, 0.99);
            LocalDateTime createdAt = ref.startTime().plusSeconds(2);

            AnomalyRecord anomaly = AnomalyRecord.builder()
                .apiLogId((long) (1000 + i))
                .endpoint(ref.endpoint())
                .method(ref.endpoint().startsWith("/api/") ? "GET" : "POST")
                .msifLstmScore(msif)
                .pleGruScore(ple)
                .hybridEnsembleScore(severityScore)
                .confidence(clamp(0.72 + jitter(0.08), 0.55, 0.99))
                .severity(severity)
                .fusionMethod("weighted_ensemble")
                .mlServiceVersion("seed-2.0.0")
                .mlProcessingTimeMs(Math.max(18L, Math.round(36 + jitter(15.0))))
                .status(status)
                .isAcknowledged("ACKNOWLEDGED".equals(status) || "RESOLVED".equals(status))
                .isResolved("RESOLVED".equals(status))
                .isFalsePositive(false)
                .traceId(ref.traceId())
                .serviceName(ref.serviceName())
                .environment("production")
                .createdBy("demo-seeder")
                .createdAt(createdAt)
                .additionalContext(Map.of(
                    "source", "demo-seeder",
                    "endpoint", ref.endpoint(),
                    "statusCode", ref.statusCode(),
                    "traceDurationMs", ref.durationMs()
                ))
                .build();

            if ("ACKNOWLEDGED".equals(status)) {
                anomaly.setAcknowledgedAt(createdAt.plusMinutes(4));
                anomaly.setAcknowledgedBy("oncall-engineer");
            }
            if ("RESOLVED".equals(status)) {
                anomaly.setAcknowledgedAt(createdAt.plusMinutes(3));
                anomaly.setAcknowledgedBy("oncall-engineer");
                anomaly.setResolvedAt(createdAt.plusMinutes(11));
                anomaly.setResolvedBy("incident-bot");
            }

            anomalyRepository.save(anomaly);
            anomalySeverityByTrace.put(ref.traceId(), severity);
            saved++;
        }

        log.info("Seeded {} demo anomalies (alerts data source)", saved);
    }

    private void seedLogs() {
        int existing;
        try {
            existing = openSearchLogService.getRecentLogs(80).size();
        } catch (Exception ex) {
            log.warn("Unable to query OpenSearch for seed check; skipping logs seed: {}", ex.getMessage());
            return;
        }

        if (existing >= 50) {
            log.info("Demo logs already present in OpenSearch ({} records), skipping seed", existing);
            return;
        }

        if (seedTraces.isEmpty()) {
            hydrateSeedTracesFromDb();
        }

        int saved = 0;
        for (int i = 0; i < LOG_TARGET; i++) {
            SeedTraceRef ref = seedTraces.get(i % seedTraces.size());
            String severity = anomalySeverityByTrace.getOrDefault(ref.traceId(), ref.statusCode() >= 500 ? "HIGH" : "LOW");
            String level = logLevelFromSeverity(severity, i);

            LogDTO logDto = new LogDTO();
            logDto.setServiceName(ref.serviceName());
            logDto.setLevel(level);
            logDto.setMessage(buildLogMessage(ref, level));
            logDto.setSource("application");
            logDto.setEnvironment("production");
            logDto.setTraceId(ref.traceId());
            logDto.setSpanId("seed-span-" + (i % TRACE_TARGET));
            logDto.setCorrelationId("corr-" + ref.serviceName() + "-" + (i % 80));
            logDto.setTimestamp(ref.startTime().minusSeconds(i % 20).toInstant(java.time.ZoneOffset.UTC));
            logDto.setMetadata(Map.of(
                "seed", true,
                "endpoint", ref.endpoint(),
                "statusCode", ref.statusCode(),
                "severity", severity
            ));

            openSearchLogService.indexLog(logDto);
            saved++;
        }

        log.info("Seeded {} demo logs into OpenSearch", saved);
    }

    private static boolean isIncidentWindow(String serviceName, int minuteIndex) {
        if ("payment-service".equals(serviceName)) {
            return minuteIndex < 12;
        }
        if ("api-gateway".equals(serviceName)) {
            return minuteIndex >= 8 && minuteIndex < 16;
        }
        return false;
    }

    private void hydrateSeedTracesFromDb() {
        List<TraceRecord> latest = traceRepository.findAllByOrderByStartTimeDesc(PageRequest.of(0, TRACE_TARGET));
        for (TraceRecord t : latest) {
            seedTraces.add(new SeedTraceRef(
                t.getTraceId(),
                t.getServiceName(),
                tagAsString(t.getTags(), "endpoint", "/unknown"),
                t.getStartTime(),
                t.getStatusCode() == null ? 200 : t.getStatusCode(),
                t.getDuration() == null ? 0L : t.getDuration()
            ));
        }
    }

    private static String tagAsString(Map<String, Object> tags, String key, String fallback) {
        if (tags == null) {
            return fallback;
        }
        Object value = tags.get(key);
        return value == null ? fallback : String.valueOf(value);
    }

    private static String logLevelFromSeverity(String severity, int idx) {
        if ("CRITICAL".equals(severity)) {
            return idx % 2 == 0 ? "CRITICAL" : "ERROR";
        }
        if ("HIGH".equals(severity)) {
            return idx % 3 == 0 ? "ERROR" : "WARN";
        }
        if ("MEDIUM".equals(severity)) {
            return idx % 2 == 0 ? "WARN" : "INFO";
        }
        return idx % 6 == 0 ? "DEBUG" : "INFO";
    }

    private static String buildLogMessage(SeedTraceRef ref, String level) {
        if ("CRITICAL".equals(level) || "ERROR".equals(level)) {
            return "" + ref.serviceName() + " failed on " + ref.endpoint()
                + " with status " + ref.statusCode() + " and latency " + ref.durationMs() + "ms";
        }
        if ("WARN".equals(level)) {
            return ref.serviceName() + " experienced elevated latency on " + ref.endpoint()
                + " (" + ref.durationMs() + "ms)";
        }
        if ("DEBUG".equals(level)) {
            return "Trace diagnostics for " + ref.serviceName() + " on " + ref.endpoint();
        }
        return ref.serviceName() + " served " + ref.endpoint() + " successfully";
    }

    private double scoreFromTrace(SeedTraceRef ref) {
        double byStatus = ref.statusCode() >= 500 ? 0.90 : (ref.statusCode() >= 400 ? 0.68 : 0.22);
        double byDuration = Math.min(ref.durationMs() / 2600.0, 0.45);
        return clamp(byStatus + byDuration + jitter(0.03), 0.05, 0.99);
    }

    private static String severityFromScore(double score) {
        if (score >= 0.85) {
            return "CRITICAL";
        }
        if (score >= 0.70) {
            return "HIGH";
        }
        if (score >= 0.45) {
            return "MEDIUM";
        }
        return "LOW";
    }

    private double jitter(double maxAbs) {
        return (random.nextDouble() * 2.0 - 1.0) * maxAbs;
    }

    private static double clamp(double value, double min, double max) {
        return Math.max(min, Math.min(max, value));
    }

    private record ServiceProfile(
        String serviceName,
        String endpoint,
        String operation,
        String team,
        int baseLatencyMs,
        int baseRpm,
        double baseErrorRate
    ) {}

    private record SeedTraceRef(
        String traceId,
        String serviceName,
        String endpoint,
        LocalDateTime startTime,
        int statusCode,
        long durationMs
    ) {}
}
