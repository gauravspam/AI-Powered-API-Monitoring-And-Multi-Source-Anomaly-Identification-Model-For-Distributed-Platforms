package com.api.monitoring.backend.service;

import com.api.monitoring.backend.dto.AnomalyResponse;
import com.api.monitoring.backend.dto.LogEntryRequest;
import com.api.monitoring.backend.dto.StatisticsResponse;
import com.api.monitoring.backend.dto.ml.PredictionResponseDto;
import com.api.monitoring.backend.model.AnomalyRecord;
import com.api.monitoring.backend.model.LogRecord;
import com.api.monitoring.backend.model.MetricRecord;
import com.api.monitoring.backend.model.TraceRecord;
import com.api.monitoring.backend.repository.AnomalyRepository;
import com.api.monitoring.backend.repository.LogRepository;
import com.api.monitoring.backend.repository.MetricRepository;
import com.api.monitoring.backend.repository.TraceRepository;
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

    @Transactional
    public AnomalyResponse detectAnomaly(LogEntryRequest logEntry) {
        try {
            // Define window (last 60 seconds)
            Instant windowEnd = Instant.now();
            Instant windowStart = windowEnd.minus(60, ChronoUnit.SECONDS);

            String serviceName = (logEntry.getServiceName() != null) ? logEntry.getServiceName()
                    : logEntry.getApiName();
            if (serviceName == null)
                serviceName = "default-service";

            log.info("Assembling window {} - {} for service {}", windowStart, windowEnd, serviceName);

            // Fetch data (Metrics, Logs, Traces) could be passed empty if handled by
            // Aggregator inside Client,
            // but keeping signature for compatibility if Client uses them.
            List<MetricRecord> metrics = metricRepository.findByCreatedAtBetween(windowStart, windowEnd);
            List<LogRecord> logs = logRepository.findByCreatedAtBetween(windowStart, windowEnd);
            List<TraceRecord> traces = traceRepository.findByCreatedAtBetween(windowStart, windowEnd);

            // Call ML Service
            PredictionResponseDto mlResponse = mlServiceClient.detectAnomaly(
                    metrics, logs, traces, serviceName, windowStart, windowEnd);

            // Handle Null Response
            if (mlResponse == null || mlResponse.getResult() == null) {
                log.warn("ML Service returned null response. Skipping anomaly save.");
                return AnomalyResponse.builder()
                        .status("UNKNOWN")
                        .serviceName(serviceName)
                        .timestamp(Instant.now().toString())
                        .build();
            }

            // Save if Anomaly
            if (mlResponse.getResult().isAnomaly()) {
                saveAnomalyRecord(mlResponse, logEntry);
            }

            return convertToAnomalyResponse(mlResponse, logEntry);

        } catch (Exception e) {
            log.error("Anomaly detection failed: {}", e.getMessage(), e);
            // Fallback response
            return AnomalyResponse.builder()
                    .status("ERROR")
                    .serviceName(logEntry.getApiName())
                    .timestamp(Instant.now().toString())
                    .build();
        }
    }

    public List<AnomalyResponse> getRecentAnomalies(int limit) {
        List<AnomalyRecord> records = anomalyRepository.findTop10ByOrderByCreatedAtDesc();
        return records.stream()
                .map(this::mapRecordToResponse)
                .collect(Collectors.toList());
    }

    @Transactional
    public boolean acknowledgeAnomaly(Long id) {
        return anomalyRepository.findById(id).map(record -> {
            record.setAcknowledged(true);
            record.setStatus("ACKNOWLEDGED");
            anomalyRepository.save(record);
            return true;
        }).orElse(false);
    }

    public StatisticsResponse getStatistics(String apiName) {
        long total = anomalyRepository.count();
        long active = anomalyRepository.count(); // TODO: filter by status='ACTIVE'
        return StatisticsResponse.builder()
                .totalAnomalies(total)
                .activeAnomalies(active)
                .accuracy(95.5) // Placeholder
                .falsePositiveRate(0.04) // Placeholder
                .build();
    }

    // --- Helper Methods ---

    private AnomalyResponse convertToAnomalyResponse(PredictionResponseDto ml, LogEntryRequest logEntry) {
        String serviceName = (logEntry.getServiceName() != null) ? logEntry.getServiceName() : logEntry.getApiName();
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
                .severity(res.getSeverity()) // FIXED: Direct string assignment
                .processingTimeMs(ml.getProcessingTimeMs())
                .timestamp(Instant.now().toString())
                .build();
    }

    private void saveAnomalyRecord(PredictionResponseDto ml, LogEntryRequest logEntry) {
        String serviceName = (logEntry.getServiceName() != null) ? logEntry.getServiceName() : logEntry.getApiName();
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
                .severity(res.getSeverity()) // FIXED: Direct string assignment
                .status("ACTIVE")
                .isAcknowledged(false)
                .isFalsePositive(false)
                .isResolved(false)
                .mlServiceVersion(ml.getModelVersion())
                .mlProcessingTimeMs(ml.getProcessingTimeMs() != null ? ml.getProcessingTimeMs().longValue() : 0L)
                .createdAt(LocalDateTime.now())
                .build();

        anomalyRepository.save(record);
        log.info("💾 Saved anomaly record: service={}, score={}", serviceName, res.getScoreFusion());
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
}
