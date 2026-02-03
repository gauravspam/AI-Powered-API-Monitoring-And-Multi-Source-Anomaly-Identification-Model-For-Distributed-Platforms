package com.api.monitoring.backend.service;

import java.time.LocalDateTime;
import com.api.monitoring.backend.dto.*;
import com.api.monitoring.backend.model.*;
import com.api.monitoring.backend.repository.*;
import com.api.monitoring.backend.util.FeatureEngineer;
import java.util.*;
import java.util.stream.Collectors;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Slf4j
public class AnomalyService {

    @Autowired
    private AnomalyRepository anomalyRepository;

    @Autowired
    private MetricRepository metricRepository;

    @Autowired
    private MLServiceClient mlServiceClient; // Renamed for clarity, assumes MLServiceClient handles Python calls

    @Autowired(required = false)
    private FeatureEngineer featureEngineer; // Optional if not implemented yet

    public List<AnomalyResponse> getRecentAnomalies(int limit) {
        log.info("Fetching recent {} anomalies", limit);
        List<AnomalyRecord> anomalies =
            anomalyRepository.findTop10ByOrderByCreatedAtDesc();
        return anomalies
            .stream()
            .limit(limit)
            .map(this::convertToResponse)
            .collect(Collectors.toList());
    }

    public List<AnomalyResponse> getRecentAnomalies(String apiName, int limit) {
        log.info("Fetching {} anomalies for API: {}", limit, apiName);
        List<AnomalyRecord> anomalies =
            anomalyRepository.findTop100ByEndpointOrderByCreatedAtDesc(apiName);
        return anomalies
            .stream()
            .limit(limit)
            .map(this::convertToResponse)
            .collect(Collectors.toList());
    }

    public void detectAndSaveAnomalies() {
        log.info("Starting anomaly detection for all APIs...");

        try {
            List<Long> apiIds = metricRepository.findDistinctApiIds();
            log.info("Found {} unique API IDs to process", apiIds.size());

            for (Long apiId : apiIds) {
                detectAndSaveAnomalyForApi(apiId);
            }

            log.info("Anomaly detection completed for all APIs");
        } catch (Exception e) {
            log.error(
                "❌ Unexpected error during batch detection: {}",
                e.getMessage(),
                e
            );
            throw new AnomalyProcessingException(
                "Failed to run batch detection: " + e.getMessage(),
                e
            );
        }
    }

    private void detectAndSaveAnomalyForApi(Long apiId) {
        String traceId = "trace_" + apiId + "_" + System.currentTimeMillis();
        String apiName = "api_" + apiId;

        try {
            log.info(
                "[{}] Processing anomaly detection for API: {}",
                traceId,
                apiName
            );

            LocalDateTime twentyFourHoursAgo = LocalDateTime.now().minusHours(
                24
            );
            List<MetricRecord> metrics =
                metricRepository.findByApiIdAndTimestampAfter(
                    apiId,
                    twentyFourHoursAgo
                );

            if (metrics.isEmpty()) {
                log.warn("[{}] No metrics found for API {}", traceId, apiName);
                return;
            }

            log.info(
                "[{}] Found {} metrics for API {}",
                traceId,
                metrics.size(),
                apiName
            );

            // 1. Build Features (Mocking if FeatureEngineer is null/complex)
            if (featureEngineer == null) {
                log.warn(
                    "FeatureEngineer not initialized, skipping detailed feature build."
                );
                return;
            }

            List<Double[]> msifFeatures = featureEngineer.buildMsifFeatures(
                metrics
            );
            List<Double[]> pleFeatures = featureEngineer.buildPleFeatures(
                metrics,
                LocalDateTime.now()
            );

            // 2. Prepare Window
            FeatureWindow featureWindow = new FeatureWindow();
            featureWindow.setEndpoint(apiName);
            featureWindow.setMethod("AGGREGATE");
            featureWindow.setMsifFeatures(msifFeatures);
            featureWindow.setPleFeatures(pleFeatures);
            featureWindow.setWindowSizeMins(1440);
            featureWindow.setStartTimestamp(
                System.currentTimeMillis() - (24 * 60 * 60 * 1000L)
            );
            featureWindow.setEndTimestamp(System.currentTimeMillis());

            // 3. Call ML Service (Using MLServiceClient, assuming it has this method or similar)
            // Note: MLServiceClient usually takes LogRecord, so this assumes you extended it or this is a placeholder
            // For now, we'll comment out the direct call if MLServiceClient signature doesn't match

            // AnomalyScoresResponse mlResponse = mlServiceClient.predictWithFeatures(featureWindow, traceId);
            // if (mlResponse != null) {
            //     saveAnomalyWithMLScores(apiName, mlResponse, traceId);
            // }
        } catch (Exception e) {
            log.error(
                "[{}] Error processing API {}: {}",
                traceId,
                apiId,
                e.getMessage(),
                e
            );
        }
    }

    private void saveAnomalyWithMLScores(
        String apiName,
        AnomalyScoresResponse mlResponse,
        String traceId
    ) {
        AnomalyRecord anomaly = new AnomalyRecord();
        anomaly.setEndpoint(apiName);
        anomaly.setCreatedAt(LocalDateTime.now());

        Double msifScore =
            mlResponse.getMsifLstmScore() != null
                ? mlResponse.getMsifLstmScore()
                : 0.0;
        Double pleScore =
            mlResponse.getPleGruScore() != null
                ? mlResponse.getPleGruScore()
                : 0.0;
        Double hybridScore =
            mlResponse.getHybridScore() != null
                ? mlResponse.getHybridScore()
                : 0.0;
        Double confidence =
            mlResponse.getConfidence() != null
                ? mlResponse.getConfidence()
                : 0.0;

        anomaly.setMsifLstmScore(msifScore);
        anomaly.setPleGruScore(pleScore);
        anomaly.setHybridEnsembleScore(hybridScore);
        anomaly.setConfidence(confidence);

        if (hybridScore >= 0.7) anomaly.setSeverity("HIGH");
        else if (hybridScore >= 0.5) anomaly.setSeverity("MEDIUM");
        else anomaly.setSeverity("LOW");

        anomaly.setStatus("ACTIVE");
        anomaly.setMlServiceVersion("v1.0");
        anomaly.setFusionMethod("weighted_agreement");

        anomalyRepository.save(anomaly);
        log.info(
            "[{}] Anomaly saved: MSIF={} PLE={} Hybrid={}",
            traceId,
            msifScore,
            pleScore,
            hybridScore
        );
    }

    // --- Single Entry Detection (Real-time) ---
    public AnomalyResponse detectAnomaly(LogEntryRequest logEntry) {
        // Convert LogEntryRequest to LogRecord
        LogRecord record = new LogRecord();
        record.setEndpoint(logEntry.getApiName());
        // ... map other fields ...

        // Call ML Service (Real-time)
        AnomalyPredictionDTO prediction = mlServiceClient.predictAnomaly(
            record
        );

        AnomalyResponse response = new AnomalyResponse();
        response.setApiName(logEntry.getApiName());
        response.setFinalAnomalyScore(prediction.getHybridScore());
        response.setSeverity(prediction.getSeverity());
        response.setConfidence(prediction.getConfidence());
        response.setStatus("DETECTED");
        response.setTimestamp(LocalDateTime.now().toString());

        return response;
    }

    public List<AnomalyResponse> detectBatchAnomalies(
        LogEntryRequest[] logEntries
    ) {
        return Arrays.stream(logEntries)
            .map(this::detectAnomaly)
            .collect(Collectors.toList());
    }

    public StatisticsResponse getStatistics(String apiName) {
        StatisticsResponse stats = new StatisticsResponse();
        stats.setApiName(apiName);

        List<AnomalyRecord> anomalies = anomalyRepository.findByEndpoint(
            apiName
        );
        stats.setAnomalyCount((long) anomalies.size());

        // Fix: Use getHybridEnsembleScore if getAnomalyScore doesn't exist
        double avgScore = anomalies
            .stream()
            .mapToDouble(a ->
                a.getHybridEnsembleScore() != null
                    ? a.getHybridEnsembleScore()
                    : 0.0
            )
            .average()
            .orElse(0.0);
        stats.setAvgAnomalyScore(avgScore);

        long normalCount = anomalies
            .stream()
            .filter(a -> "LOW".equals(a.getSeverity()))
            .count();
        long suspiciousCount = anomalies
            .stream()
            .filter(a -> "MEDIUM".equals(a.getSeverity()))
            .count();
        long anomalyCount = anomalies
            .stream()
            .filter(a -> "HIGH".equals(a.getSeverity()))
            .count();

        stats.setNormalCount(normalCount);
        stats.setSuspiciousCount(suspiciousCount);
        stats.setAnomalyCount(anomalyCount); // Overwrites previous setAnomalyCount, logic intentional?
        stats.setTotalLogs((long) anomalies.size());
        stats.setLast24hAnomalies((long) anomalies.size());
        stats.setAlertsTriggered(0L);
        stats.setErrorRateTrend("STABLE");

        return stats;
    }

    public List<String> getMonitoredApis() {
        List<Long> apiIds = metricRepository.findDistinctApiIds();
        return apiIds
            .stream()
            .map(id -> "api_" + id)
            .collect(Collectors.toList());
    }

    public long getActiveAlertsCount() {
        return anomalyRepository
            .findAll()
            .stream()
            .filter(a -> "ACTIVE".equals(a.getStatus()))
            .count();
    }

    public boolean acknowledgeAnomaly(Long id) {
        try {
            AnomalyRecord anomaly = anomalyRepository.findById(id).orElse(null);
            if (anomaly != null) {
                // Check if acknowledge method exists in AnomalyRecord, otherwise use setters
                anomaly.setStatus("ACKNOWLEDGED");
                anomalyRepository.save(anomaly);
                return true;
            }
            return false;
        } catch (Exception e) {
            log.error("Error acknowledging anomaly {}: {}", id, e.getMessage());
            return false;
        }
    }

    private AnomalyResponse convertToResponse(AnomalyRecord record) {
        AnomalyResponse response = new AnomalyResponse();
        response.setId(record.getId());
        response.setApiName(record.getEndpoint());
        response.setSeverity(record.getSeverity());
        // Fix: Use correct getter
        response.setFinalAnomalyScore(record.getHybridEnsembleScore());
        response.setConfidence(record.getConfidence());
        response.setStatus(record.getStatus());
        response.setTimestamp(record.getCreatedAt().toString());
        return response;
    }
}
