package com.api.monitoring.backend.service;

import com.api.monitoring.backend.dto.AnomalyResponse;
import com.api.monitoring.backend.dto.LogEntryRequest;
import com.api.monitoring.backend.dto.StatisticsResponse;
import com.api.monitoring.backend.dto.ml.PredictionResponseDto; // ✅ ADDED
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

            log.info("Assembling window: {} - {} for service: {}", windowStart, windowEnd, serviceName);

            // Fetch recent data
            List<MetricRecord> metrics = metricRepository.findByCreatedAtBetween(windowStart, windowEnd);
            List<LogRecord> logs = logRepository.findByCreatedAtBetween(windowStart, windowEnd);
            List<TraceRecord> traces = traceRepository.findByCreatedAtBetween(windowStart, windowEnd);

            log.debug("Window contents: {} metrics, {} logs, {} traces", metrics.size(), logs.size(), traces.size());

            // Call ML service (V2)
            PredictionResponseDto mlResponse = mlServiceClient.detectAnomaly(
                    metrics, logs, traces,
                    serviceName,
                    windowStart, windowEnd);

            // Check if result exists (handle fallback/error cases)
            if (mlResponse == null || mlResponse.getResult() == null) {
                log.warn("ML Service returned null response. Skipping anomaly save.");
                return AnomalyResponse.builder()
                        .status("UNKNOWN")
                        .serviceName(serviceName)
                        .timestamp(Instant.now().toString())
                        .build();
            }

            // Convert to frontend response
            AnomalyResponse response = convertToAnomalyResponse(mlResponse, logEntry);

            // Save anomaly record if detected
            if (mlResponse.getResult().isAnomaly()) {
                saveAnomalyRecord(mlResponse, logEntry);
            }

            return response;

        } catch (Exception e) {
            log.error("Anomaly detection failed: {}", e.getMessage(), e);
            // Return safe fallback instead of throwing to keep API alive
            return AnomalyResponse.builder().status("ERROR").build();
        }
    }

    /**
     * Get recent anomalies for dashboard.
     */
    public List<AnomalyResponse> getRecentAnomalies(int limit) {
        // Limitation: Repository might not support 'limit' natively without Pageable
        // Using Top10 for now as per original code
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
        long active = anomalyRepository.count(); // TODO: filter by status

        return StatisticsResponse.builder()
                .totalAnomalies(total)
                .activeAnomalies(active)
                .accuracy(95.5) // Placeholder
                .falsePositiveRate(0.04) // Placeholder
                .build();
    }

    // --- Helper Methods ---

    private AnomalyResponse convertToAnomalyResponse(PredictionResponseDto ml, LogEntryRequest logEntry) {
        String serviceName = logEntry.getServiceName() != null ? logEntry.getServiceName() : logEntry.getApiName();
        PredictionResponseDto.AnomalyScoreResult res = ml.getResult();

        return AnomalyResponse.builder()
                .serviceName(serviceName)
                .endpoint(logEntry.getEndpoint())
                .status(res.isAnomaly() ? "ANOMALY" : "NORMAL")
                .finalAnomalyScore(res.getScoreFusion())
                .msifScore(res.getScoreMsif())
                .pleScore(res.getScorePle())
                .confidence(res.getConfidence())
                .fusionMethod("weighted_fusion_v2")
                .severity(determineSeverity(res.getSeverity()))
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
                .severity(record.getSeverity())
                .confidence(record.getConfidence())
                .timestamp(record.getCreatedAt().toString())
                .build();
    }

    private void saveAnomalyRecord(PredictionResponseDto ml, LogEntryRequest logEntry) {
        String serviceName = logEntry.getServiceName() != null ? logEntry.getServiceName() : logEntry.getApiName();
        PredictionResponseDto.AnomalyScoreResult res = ml.getResult();

        AnomalyRecord record = AnomalyRecord.builder()
                .serviceName(serviceName)
                .endpoint(logEntry.getEndpoint())
                .method(logEntry.getMethod() != null ? logEntry.getMethod() : "UNKNOWN")
                .msifLstmScore(res.getScoreMsif())
                .pleGruScore(res.getScorePle())
                .hybridEnsembleScore(res.getScoreFusion())
                .fusionMethod("weighted_fusion_v2")
                .confidence(res.getConfidence())
                .severity(determineSeverity(res.getSeverity()))
                .status("ACTIVE")
                .isAcknowledged(false)
                .isFalsePositive(false)
                .isResolved(false)
                .mlServiceVersion(ml.getModelVersion())
                .mlProcessingTimeMs(ml.getProcessingTimeMs().longValue())
                .createdAt(LocalDateTime.now())
                .build();

        anomalyRepository.save(record);
        log.info("Saved anomaly record: service={}, score={}", serviceName, res.getScoreFusion());
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
