package com.api.monitoring.backend.service;

import com.api.monitoring.backend.dto.AnomalyPredictionDTO;
import com.api.monitoring.backend.model.AnomalyRecord;
import com.api.monitoring.backend.model.LogRecord;
import com.api.monitoring.backend.repository.AnomalyRepository;
import com.api.monitoring.backend.repository.LogRepository;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Slf4j
public class AnomalyService {

    private final MLServiceClient mlServiceClient;
    private final AnomalyRepository anomalyRepository;
    private final LogRepository logRepository;

    @Autowired
    public AnomalyService(
        MLServiceClient mlServiceClient,
        AnomalyRepository anomalyRepository,
        LogRepository logRepository
    ) {
        this.mlServiceClient = mlServiceClient;
        this.anomalyRepository = anomalyRepository;
        this.logRepository = logRepository;
    }

    @Transactional
    public AnomalyRecord analyzeApiLog(LogRecord logRecord) {
        long startTime = System.currentTimeMillis();

        try {
            log.info(
                "🔍 Analyzing log ID: {}, endpoint: {}",
                logRecord.getId(),
                logRecord.getEndpoint()
            );

            if (logRecord == null) {
                throw new IllegalArgumentException("LogRecord cannot be null");
            }

            if (logRecord.getId() == null) {
                throw new IllegalArgumentException(
                    "LogRecord must be persisted (ID cannot be null)"
                );
            }

            if (Boolean.TRUE.equals(logRecord.getProcessed())) {
                log.warn(
                    "⚠️ Log {} already processed. Skipping.",
                    logRecord.getId()
                );
                return anomalyRepository
                    .findById(logRecord.getAnomalyId())
                    .orElse(null);
            }

            AnomalyPredictionDTO prediction = mlServiceClient.predictAnomaly(
                logRecord
            );

            AnomalyRecord anomalyRecord = AnomalyRecord.builder()
                .endpoint(logRecord.getEndpoint())
                .method(logRecord.getMethod())
                .msifLstmScore(prediction.getMsifScore())
                .pleGruScore(prediction.getPleScore())
                .hybridEnsembleScore(prediction.getHybridScore())
                .confidence(prediction.getConfidence())
                .severity(prediction.getSeverity())
                .fusionMethod(prediction.getFusionMethod())
                .status("ACTIVE")
                .acknowledged(false)
                .traceId(logRecord.getTraceId())
                .mlProcessingTimeMs(prediction.getMlProcessingTimeMs())
                .mlServiceVersion(prediction.getMlServiceVersion())
                .build();

            AnomalyRecord savedAnomaly = anomalyRepository.save(anomalyRecord);
            log.info(
                "✅ Anomaly record created: ID={}, hybrid_score={}, severity={}",
                savedAnomaly.getId(),
                savedAnomaly.getHybridEnsembleScore(),
                savedAnomaly.getSeverity()
            );

            logRecord.markAsProcessed(
                savedAnomaly.getId(),
                prediction.getMlServiceVersion()
            );
            logRepository.save(logRecord);

            long totalDuration = System.currentTimeMillis() - startTime;
            log.info(
                "✅ Log {} analysis complete in {}ms (ML: {}ms)",
                logRecord.getId(),
                totalDuration,
                prediction.getMlProcessingTimeMs()
            );

            return savedAnomaly;
        } catch (MLServiceClient.MLServiceException e) {
            log.error(
                "❌ ML Service error analyzing log {}: {}",
                logRecord.getId(),
                e.getMessage()
            );
            throw new AnomalyProcessingException(
                "ML service failed: " + e.getMessage(),
                e
            );
        } catch (Exception e) {
            log.error(
                "❌ Unexpected error analyzing log {}: {}",
                logRecord.getId(),
                e.getMessage(),
                e
            );
            throw new AnomalyProcessingException(
                "Failed to analyze log: " + e.getMessage(),
                e
            );
        }
    }

    @Transactional
    public List<AnomalyRecord> analyzeLogBatch(List<LogRecord> logs) {
        log.info("📦 Batch analyzing {} logs", logs.size());

        return logs
            .stream()
            .map(logRecord -> {
                try {
                    return analyzeApiLog(logRecord);
                } catch (Exception e) {
                    log.error(
                        "Failed to analyze log {}: {}",
                        logRecord.getId(),
                        e.getMessage()
                    );
                    return null;
                }
            })
            .filter(anomaly -> anomaly != null)
            .toList();
    }

    public List<AnomalyRecord> getRecentAnomalies(int minutes) {
        LocalDateTime since = LocalDateTime.now().minusMinutes(minutes);
        return anomalyRepository.findRecentAnomalies(since);
    }

    public List<AnomalyRecord> getAnomaliesBySeverity(String severity) {
        return anomalyRepository.findBySeverityOrderByCreatedAtDesc(severity);
    }

    public List<AnomalyRecord> getCriticalAnomalies(int limit) {
        List<String> severities = List.of("CRITICAL", "HIGH");
        Pageable pageable = PageRequest.of(0, limit);
        return anomalyRepository
            .findBySeverityInOrderByCreatedAtDesc(severities, pageable)
            .getContent();
    }

    public List<AnomalyRecord> getUnacknowledgedCritical() {
        return anomalyRepository.findUnacknowledgedCritical();
    }

    @Transactional
    public AnomalyRecord acknowledgeAnomaly(Long anomalyId, String username) {
        AnomalyRecord anomaly = anomalyRepository
            .findById(anomalyId)
            .orElseThrow(() ->
                new IllegalArgumentException("Anomaly not found: " + anomalyId)
            );

        anomaly.acknowledge(username);
        AnomalyRecord saved = anomalyRepository.save(anomaly);

        log.info("✅ Anomaly {} acknowledged by {}", anomalyId, username);
        return saved;
    }

    @Transactional
    public AnomalyRecord resolveAnomaly(Long anomalyId) {
        AnomalyRecord anomaly = anomalyRepository
            .findById(anomalyId)
            .orElseThrow(() ->
                new IllegalArgumentException("Anomaly not found: " + anomalyId)
            );

        anomaly.resolve();
        AnomalyRecord saved = anomalyRepository.save(anomaly);

        log.info("✅ Anomaly {} resolved", anomalyId);
        return saved;
    }

    public Map<String, Long> getAnomalyStatistics(int hours) {
        LocalDateTime since = LocalDateTime.now().minusHours(hours);

        long totalCount = anomalyRepository.countByCreatedAtAfter(since);
        long criticalCount = anomalyRepository.countBySeverityAndCreatedAtAfter(
            "CRITICAL",
            since
        );
        long highCount = anomalyRepository.countBySeverityAndCreatedAtAfter(
            "HIGH",
            since
        );
        long mediumCount = anomalyRepository.countBySeverityAndCreatedAtAfter(
            "MEDIUM",
            since
        );
        long lowCount = anomalyRepository.countBySeverityAndCreatedAtAfter(
            "LOW",
            since
        );

        return Map.of(
            "total",
            totalCount,
            "critical",
            criticalCount,
            "high",
            highCount,
            "medium",
            mediumCount,
            "low",
            lowCount
        );
    }

    public static class AnomalyProcessingException extends RuntimeException {

        public AnomalyProcessingException(String message) {
            super(message);
        }

        public AnomalyProcessingException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
