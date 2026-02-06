package com.api.monitoring.backend.service;

import com.api.monitoring.backend.dto.AnomalyPredictionDTO;
import com.api.monitoring.backend.dto.AnomalyResponse;
import com.api.monitoring.backend.dto.LogEntryRequest;
import com.api.monitoring.backend.dto.StatisticsResponse;
import com.api.monitoring.backend.model.AnomalyRecord;
import com.api.monitoring.backend.model.LogRecord;
import com.api.monitoring.backend.repository.AnomalyRepository;
import com.api.monitoring.backend.repository.MetricRepository;
import com.api.monitoring.backend.util.FeatureEngineer;
import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.stream.Collectors;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Slf4j
public class AnomalyService {

    private static final double SAVE_THRESHOLD = 0.40;

    private static final double TH_LOW = 0.30;
    private static final double TH_MEDIUM = 0.50;
    private static final double TH_HIGH = 0.70;
    private static final double TH_CRITICAL = 0.85;

    private final AnomalyRepository anomalyRepository;
    private final MetricRepository metricRepository;
    private final MLServiceClient mlServiceClient;

    @Autowired(required = false)
    private FeatureEngineer featureEngineer;

    @Autowired
    public AnomalyService(
            AnomalyRepository anomalyRepository,
            MetricRepository metricRepository,
            MLServiceClient mlServiceClient) {
        this.anomalyRepository = anomalyRepository;
        this.metricRepository = metricRepository;
        this.mlServiceClient = mlServiceClient;
    }

    public List<AnomalyResponse> getRecentAnomalies(int limit) {
        int safeLimit = Math.max(1, Math.min(limit, 200));
        log.info("Fetching recent anomalies, limit={}", safeLimit);

        List<AnomalyRecord> anomalies = anomalyRepository.findTop10ByOrderByCreatedAtDesc();
        return anomalies.stream()
                .limit(safeLimit)
                .map(this::convertToResponse)
                .collect(Collectors.toList());
    }

    public List<AnomalyResponse> getRecentAnomalies(String apiName, int limit) {
        int safeLimit = Math.max(1, Math.min(limit, 200));
        String endpoint = (apiName == null) ? "" : apiName;

        log.info("Fetching anomalies for API={}, limit={}", endpoint, safeLimit);

        List<AnomalyRecord> anomalies = anomalyRepository.findTop100ByEndpointOrderByCreatedAtDesc(endpoint);
        return anomalies.stream()
                .limit(safeLimit)
                .map(this::convertToResponse)
                .collect(Collectors.toList());
    }

    /**
     * Real-time anomaly detection (called by AnomalyController
     * /api/anomalies/analyze).
     */
    @Transactional
    public AnomalyResponse detectAnomaly(LogEntryRequest logEntry) {
        Objects.requireNonNull(logEntry, "logEntry must not be null");
        String endpoint = logEntry.getApiName();

        LogRecord record = LogRecord.builder()
                .endpoint(endpoint)
                .method(normalizeHttpMethod(logEntry.getMethod()))
                .statusCode(defaultIfNull(logEntry.getStatusCode(), 200))
                .responseTimeMs(doubleToLongMs(defaultIfNull(logEntry.getResponseTime(), 0.0)))
                .requestCount(defaultIfNull(logEntry.getRequestCount(), 1))
                .errorRate(defaultIfNull(logEntry.getErrorRate(), 0.0))
                .cpuUsage(defaultIfNull(logEntry.getCpuUsage(), 0.0))
                .memoryUsage(defaultIfNull(logEntry.getMemoryUsage(), 0.0))
                .networkIo(doubleToLong(defaultIfNull(logEntry.getNetworkIo(), 0.0)))
                .diskIo(doubleToLong(defaultIfNull(logEntry.getDiskIo(), 0.0)))
                .hourOfDay(logEntry.getHourOfDay())
                .dayOfWeek(logEntry.getDayOfWeek())
                // apilogs.servicename is marked nullable=false in your entity; keep a default
                .serviceName("api-monitoring")
                .build();

        AnomalyPredictionDTO prediction;
        try {
            prediction = mlServiceClient.predictAnomaly(record);
        } catch (Exception e) {
            log.error("ML prediction failed for endpoint={}: {}", endpoint, e.getMessage(), e);
            throw new AnomalyProcessingException("ML prediction failed: " + e.getMessage(), e);
        }

        if (prediction == null) {
            throw new AnomalyProcessingException("ML prediction returned null response");
        }

        Double hybrid = prediction.getHybridScore();
        if (hybrid == null)
            hybrid = 0.0;

        Double msif = prediction.getMsifScore();
        if (msif == null)
            msif = 0.0;

        Double ple = prediction.getPleScore();
        if (ple == null)
            ple = 0.0;

        String severity = prediction.getSeverity();
        if (severity == null || severity.isBlank()) {
            severity = severityFromScore(hybrid);
        }

        Double confidence = prediction.getConfidence();
        if (confidence == null)
            confidence = 0.0;

        String fusionMethod = prediction.getFusionMethod();
        if (fusionMethod == null || fusionMethod.isBlank())
            fusionMethod = "weighted_ensemble";

        String mlServiceVersion = prediction.getMlServiceVersion();
        if (mlServiceVersion == null || mlServiceVersion.isBlank())
            mlServiceVersion = "1.0.0";

        Long processingTimeMs = prediction.getMlProcessingTimeMs();
        if (processingTimeMs == null)
            processingTimeMs = 0L;

        String traceId = prediction.getTraceId();

        // Save anomalies above threshold (tunable)
        if (hybrid >= SAVE_THRESHOLD) {
            try {
                AnomalyRecord anomalyRecord = AnomalyRecord.builder()
                        .endpoint(endpoint)
                        .method(record.getMethod())
                        .msifLstmScore(msif)
                        .pleGruScore(ple)
                        .hybridEnsembleScore(hybrid)
                        .confidence(confidence)
                        .severity(severity)
                        .fusionMethod(fusionMethod)
                        .mlServiceVersion(mlServiceVersion)
                        .mlProcessingTimeMs(processingTimeMs)
                        .status("ACTIVE")
                        .isAcknowledged(false)
                        .isResolved(false)
                        .isFalsePositive(false)
                        .traceId(traceId)
                        .serviceName("api-monitoring")
                        .environment("production")
                        .createdAt(LocalDateTime.now())
                        .createdBy("system")
                        .build();

                AnomalyRecord saved = anomalyRepository.save(anomalyRecord);
                log.info("Anomaly saved id={}, endpoint={}, score={}, severity={}",
                        saved.getId(), saved.getEndpoint(), saved.getHybridEnsembleScore(), saved.getSeverity());
            } catch (Exception e) {
                // Don't fail the request if DB write fails; return prediction to caller
                log.error("Failed to save anomaly to DB for endpoint={}: {}", endpoint, e.getMessage(), e);
            }
        }

        AnomalyResponse response = new AnomalyResponse();
        response.setApiName(endpoint);
        response.setFinalAnomalyScore(hybrid);
        response.setSeverity(severity);
        response.setConfidence(confidence);
        response.setStatus("DETECTED");
        response.setTimestamp(LocalDateTime.now().toString());
        return response;
    }

    public StatisticsResponse getStatistics(String apiName) {
        String endpoint = (apiName == null) ? "" : apiName;

        StatisticsResponse stats = new StatisticsResponse();
        stats.setApiName(endpoint);

        List<AnomalyRecord> anomalies = anomalyRepository.findByEndpoint(endpoint);

        stats.setTotalLogs((long) anomalies.size());

        long low = anomalies.stream().filter(a -> "LOW".equalsIgnoreCase(a.getSeverity())).count();
        long medium = anomalies.stream().filter(a -> "MEDIUM".equalsIgnoreCase(a.getSeverity())).count();
        long high = anomalies.stream().filter(a -> "HIGH".equalsIgnoreCase(a.getSeverity())).count();
        long critical = anomalies.stream().filter(a -> "CRITICAL".equalsIgnoreCase(a.getSeverity())).count();

        stats.setNormalCount(low);
        stats.setSuspiciousCount(medium);

        // Treat HIGH + CRITICAL as "anomalycount" for dashboard aggregation
        stats.setAnomalyCount(high + critical);

        double avgScore = anomalies.stream()
                .map(AnomalyRecord::getHybridEnsembleScore)
                .filter(Objects::nonNull)
                .mapToDouble(Double::doubleValue)
                .average()
                .orElse(0.0);
        stats.setAvgAnomalyScore(avgScore);

        stats.setLast24hAnomalies((long) anomalies.size());
        stats.setAlertsTriggered(0L);
        stats.setErrorRateTrend("STABLE");

        return stats;
    }

    @Transactional
    public boolean acknowledgeAnomaly(Long id) {
        if (id == null)
            return false;

        try {
            AnomalyRecord anomaly = anomalyRepository.findById(id).orElse(null);
            if (anomaly == null)
                return false;

            // Mark acknowledged boolean + set a status string used by controller filter
            // logic
            anomaly.acknowledge("system");
            anomaly.setStatus("ACKNOWLEDGED");

            anomalyRepository.save(anomaly);
            return true;
        } catch (Exception e) {
            log.error("Error acknowledging anomaly id={}: {}", id, e.getMessage(), e);
            return false;
        }
    }

    public long getActiveAlertsCount() {
        return anomalyRepository.findAll().stream()
                .filter(a -> "ACTIVE".equalsIgnoreCase(a.getStatus()))
                .count();
    }

    public List<String> getMonitoredApis() {
        List<Long> apiIds = metricRepository.findDistinctApiLogIds();
        return apiIds.stream()
                .map(id -> "api-" + id)
                .collect(Collectors.toList());
    }

    private AnomalyResponse convertToResponse(AnomalyRecord record) {
        AnomalyResponse response = new AnomalyResponse();
        response.setId(record.getId());
        response.setApiName(record.getEndpoint());
        response.setSeverity(record.getSeverity());
        response.setFinalAnomalyScore(record.getHybridEnsembleScore());
        response.setConfidence(record.getConfidence());
        response.setStatus(record.getStatus());
        response.setTimestamp(record.getCreatedAt() != null ? record.getCreatedAt().toString() : null);
        return response;
    }

    private static String normalizeHttpMethod(String method) {
        if (method == null || method.isBlank())
            return "POST";
        return method.trim().toUpperCase(Locale.ROOT);
    }

    private static String severityFromScore(double score) {
        if (score < TH_LOW)
            return "LOW";
        if (score < TH_MEDIUM)
            return "MEDIUM";
        if (score < TH_HIGH)
            return "HIGH";
        return (score >= TH_CRITICAL) ? "CRITICAL" : "HIGH";
    }

    private static long doubleToLongMs(double val) {
        if (Double.isNaN(val) || Double.isInfinite(val))
            return 0L;
        return Math.max(0L, (long) val);
    }

    private static long doubleToLong(double val) {
        if (Double.isNaN(val) || Double.isInfinite(val))
            return 0L;
        return (long) Math.max(0.0, val);
    }

    private static <T> T defaultIfNull(T value, T defaultValue) {
        return value != null ? value : defaultValue;
    }
}
