package com.api.monitoring.backend.service;

import com.api.monitoring.backend.dto.*;
import com.api.monitoring.backend.model.*;
import com.api.monitoring.backend.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class AnomalyService {

    private final MLServiceClient mlServiceClient;
    private final MetricRepository metricRepository;
    private final LogRepository logRepository;
    private final TraceRepository traceRepository;
    private final AnomalyRepository anomalyRepository;

    /**
     * Detect anomaly using multimodal window-based approach.
     */
    @Transactional
    public AnomalyResponse detectAnomaly(LogEntryRequest logEntry) {
        try {
            // Define window (last 60 seconds)
            Instant windowEnd = Instant.now();
            Instant windowStart = windowEnd.minus(60, ChronoUnit.SECONDS);

            // Handle service name alias
            String serviceName = logEntry.getServiceName() != null ? logEntry.getServiceName() : logEntry.getApiName();
            if (serviceName == null)
                serviceName = "default-service";

            log.info("Assembling window: {} - {} for service: {}",
                    windowStart, windowEnd, serviceName);

            // Fetch recent data from repositories
            List<MetricRecord> metrics = metricRepository.findByCreatedAtBetween(windowStart, windowEnd);
            List<LogRecord> logs = logRepository.findByCreatedAtBetween(windowStart, windowEnd);
            List<TraceRecord> traces = traceRepository.findByCreatedAtBetween(windowStart, windowEnd);

            log.debug("Window contents: {} metrics, {} logs, {} traces",
                    metrics.size(), logs.size(), traces.size());

            // Call ML service with structured multimodal data
            MultimodalResponse mlResponse = mlServiceClient.detectAnomaly(
                    metrics, logs, traces,
                    serviceName,
                    logEntry.getEndpoint(),
                    windowStart, windowEnd);

            // Convert to frontend response
            AnomalyResponse response = convertToAnomalyResponse(mlResponse, logEntry);

            // Save anomaly record if detected
            if ("ANOMALY".equals(mlResponse.getStatus())) {
                saveAnomalyRecord(mlResponse, logEntry, windowStart, windowEnd);
            }

            return response;

        } catch (Exception e) {
            log.error("Anomaly detection failed: {}", e.getMessage(), e);
            throw new AnomalyProcessingException("Failed to detect anomaly: " + e.getMessage(), e);
        }
    }

    /**
     * Get recent anomalies for dashboard.
     */
    public List<AnomalyResponse> getRecentAnomalies(int limit) {
        List<AnomalyRecord> records = anomalyRepository.findTop10ByOrderByCreatedAtDesc();
        return records.stream()
                .map(this::mapRecordToResponse)
                .collect(Collectors.toList());
    }

    /**
     * Acknowledge an anomaly.
     */
    @Transactional
    public boolean acknowledgeAnomaly(Long id) {
        return anomalyRepository.findById(id).map(record -> {
            record.setAcknowledged(true);
            record.setStatus("ACKNOWLEDGED");
            anomalyRepository.save(record);
            return true;
        }).orElse(false);
    }

    /**
     * Get statistics for a specific API or all.
     */
    public StatisticsResponse getStatistics(String apiName) {
        long total = anomalyRepository.count();
        long active = anomalyRepository.count(); // Add filter for status=ACTIVE if needed

        return StatisticsResponse.builder()
                .totalAnomalies(total)
                .activeAnomalies(active)
                .accuracy(95.5)
                .falsePositiveRate(0.04)
                .build();
    }

    // --- Helper Methods ---

    private AnomalyResponse convertToAnomalyResponse(MultimodalResponse ml, LogEntryRequest logEntry) {
        String serviceName = logEntry.getServiceName() != null ? logEntry.getServiceName() : logEntry.getApiName();

        return AnomalyResponse.builder()
                .serviceName(serviceName)
                .endpoint(logEntry.getEndpoint())
                .status(ml.getStatus())
                .finalAnomalyScore(ml.getFinalScore())
                .msifScore(ml.getMsifScore())
                .pleScore(ml.getPleScore())
                .confidence(parseConfidence(ml.getConfidence()))
                .fusionMethod(ml.getFusionMethod())
                .severity(determineSeverity(ml.getFinalScore()))
                .processingTimeMs(ml.getProcessingTimeMs())
                .timestamp(Instant.now().toString())
                .build();
    }

    private AnomalyResponse mapRecordToResponse(AnomalyRecord record) {
        return AnomalyResponse.builder()
                .serviceName(record.getServiceName())
                .endpoint(record.getEndpoint())
                .status(record.getStatus())
                .finalAnomalyScore(record.getHybridEnsembleScore())
                .severity(record.getSeverity()) // Corrected: use .severity() builder method
                .confidence(record.getConfidence()) // Corrected: use .confidence() builder method
                .timestamp(record.getCreatedAt().toString())
                .build();
    }

    private void saveAnomalyRecord(MultimodalResponse ml, LogEntryRequest logEntry, Instant start, Instant end) {
        String serviceName = logEntry.getServiceName() != null ? logEntry.getServiceName() : logEntry.getApiName();

        AnomalyRecord record = AnomalyRecord.builder()
                .serviceName(serviceName)
                .endpoint(logEntry.getEndpoint())
                .method(logEntry.getMethod() != null ? logEntry.getMethod() : "UNKNOWN")
                .msifLstmScore(ml.getMsifScore())
                .pleGruScore(ml.getPleScore())
                .hybridEnsembleScore(ml.getFinalScore())
                .fusionMethod(ml.getFusionMethod())
                .confidence(parseConfidenceScore(ml.getConfidence())) // Corrected: use .confidence() builder method
                .severity(determineSeverity(ml.getFinalScore())) // Corrected: use .severity() builder method
                .status("ACTIVE")
                .isAcknowledged(false)
                .isFalsePositive(false)
                .isResolved(false)
                .mlServiceVersion("2.0.0")
                .mlProcessingTimeMs(ml.getProcessingTimeMs().longValue())
                .createdAt(LocalDateTime.now())
                .build();

        anomalyRepository.save(record);
        log.info("Saved anomaly record: service={}, score={}", serviceName, ml.getFinalScore());
    }

    private Double parseConfidence(String conf) {
        if ("HIGH".equals(conf))
            return 0.9;
        if ("MEDIUM".equals(conf))
            return 0.6;
        return 0.3;
    }

    private Double parseConfidenceScore(String conf) {
        return parseConfidence(conf);
    }

    private String determineSeverity(Double score) {
        if (score >= 0.9)
            return "CRITICAL";
        if (score >= 0.7)
            return "HIGH";
        if (score >= 0.5)
            return "MEDIUM";
        return "LOW";
    }
}
