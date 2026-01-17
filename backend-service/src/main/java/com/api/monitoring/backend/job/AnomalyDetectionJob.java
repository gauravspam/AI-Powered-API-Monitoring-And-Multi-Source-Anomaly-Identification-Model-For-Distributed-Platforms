package com.api.monitoring.backend.job;

import com.api.monitoring.backend.dto.AnomalyScoresResponse;
import com.api.monitoring.backend.dto.FeatureWindow;
import com.api.monitoring.backend.model.AnomalyRecord;
import com.api.monitoring.backend.model.MetricRecord;
import com.api.monitoring.backend.repository.AnomalyRepository;
import com.api.monitoring.backend.repository.MetricRepository;
import com.api.monitoring.backend.service.PythonMLService;
import com.api.monitoring.backend.util.FeatureEngineer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Scheduled job that runs every 5 minutes
 * Queries metrics, builds features, calls ML service, saves anomaly scores
 */
@Component
public class AnomalyDetectionJob {

    private static final Logger logger = LoggerFactory.getLogger(AnomalyDetectionJob.class);

    private final MetricRepository metricRepository;
    private final AnomalyRepository anomalyRepository;
    private final PythonMLService pythonMLService;
    private final FeatureEngineer featureEngineer;

    public AnomalyDetectionJob(
            MetricRepository metricRepository,
            AnomalyRepository anomalyRepository,
            PythonMLService pythonMLService,
            FeatureEngineer featureEngineer) {
        this.metricRepository = metricRepository;
        this.anomalyRepository = anomalyRepository;
        this.pythonMLService = pythonMLService;
        this.featureEngineer = featureEngineer;
    }

    /**
     * Main job: Run every 5 minutes
     * Logic:
     * 1. Query metrics from last 5 minutes
     * 2. Group by apiId
     * 3. Build feature windows
     * 4. Call ML service
     * 5. Save anomaly scores
     * 6. Log metrics
     */
    @Scheduled(fixedDelay = 300000) // 5 minutes in milliseconds
    public void processRecentMetrics() {
        String jobId = UUID.randomUUID().toString().substring(0, 8);
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime fiveMinutesAgo = now.minusMinutes(5);

        logger.info("[{}] Starting AnomalyDetectionJob", jobId);
        long startTime = System.currentTimeMillis();

        try {
            // Step 1: Query recent metrics
            List<MetricRecord> recentMetrics = metricRepository.findByTimestampAfter(fiveMinutesAgo);

            if (recentMetrics.isEmpty()) {
                logger.info("[{}] No recent metrics found in last 5 minutes", jobId);
                return;
            }

            logger.info("[{}] Found {} metrics in last 5 minutes", jobId, recentMetrics.size());

            // Step 2: Group by apiId
            Map<Long, List<MetricRecord>> groupedMetrics = recentMetrics.stream()
                    .filter(m -> m.getApiId() != null)
                    .collect(Collectors.groupingBy(MetricRecord::getApiId));

            logger.info("[{}] Processing {} unique APIs", jobId, groupedMetrics.size());

            int successCount = 0;
            int failureCount = 0;

            // Step 3-5: For each API, predict anomalies
            for (Map.Entry<Long, List<MetricRecord>> entry : groupedMetrics.entrySet()) {
                Long apiId = entry.getKey();
                List<MetricRecord> metrics = entry.getValue();

                try {
                    // Build feature windows
                    List<Double[]> msifFeatures = featureEngineer.buildMsifFeatures(metrics);
                    List<Double[]> pleFeatures = featureEngineer.buildPleFeatures(metrics, now);

                    FeatureWindow window = new FeatureWindow(
                            "api_" + apiId, // endpoint name
                            "AGGREGATE", // method
                            msifFeatures,
                            pleFeatures,
                            60 // lookback window in minutes
                    );

                    // Call ML service (use enhanced predictWithFeatures method)
                    AnomalyScoresResponse predictions = pythonMLService.predictWithFeatures(window, jobId);

                    // Save to database
                    AnomalyRecord anomalyRecord = new AnomalyRecord();
                    anomalyRecord.setApiName("API_" + apiId);
                    anomalyRecord.setTimestamp(now);

                    // Map scores to existing fields
                    if (predictions.getMsifLstmScore() != null) {
                        anomalyRecord.setMsifLstmScore(predictions.getMsifLstmScore());
                    }
                    if (predictions.getPleGruScore() != null) {
                        anomalyRecord.setPleGruScore(predictions.getPleGruScore());
                    }
                    if (predictions.getHybridScore() != null) {
                        anomalyRecord.setHybridScore(predictions.getHybridScore());
                        anomalyRecord.setFinalAnomalyScore(predictions.getHybridScore());
                    }
                    if (predictions.getConfidence() != null) {
                        anomalyRecord.setConfidence(predictions.getConfidence());
                    }

                    // Set severity based on hybrid score
                    Double hybridScore = predictions.getHybridScore() != null ? predictions.getHybridScore() : 0.0;
                    anomalyRecord.setSeverity(mapSeverity(hybridScore));

                    // Set status
                    anomalyRecord.setStatus("ACTIVE");
                    anomalyRecord.setAcknowledged(false);

                    // Set model used
                    anomalyRecord.setMlModelUsed(
                            predictions.getFusionMethod() != null ? predictions.getFusionMethod() : "MSIF-PLE-Hybrid");

                    // Set timestamps
                    anomalyRecord.setCreatedAt(now);

                    anomalyRepository.save(anomalyRecord);

                    logger.info("[{}] Saved anomaly score for API {} - hybrid: {}",
                            jobId, apiId, String.format("%.3f", hybridScore));

                    successCount++;

                } catch (Exception e) {
                    logger.error("[{}] Error processing API {}: {}", jobId, apiId, e.getMessage(), e);
                    failureCount++;
                }
            }

            long duration = System.currentTimeMillis() - startTime;
            logger.info("[{}] AnomalyDetectionJob completed in {}ms. Success: {}, Failures: {}",
                    jobId, duration, successCount, failureCount);

        } catch (Exception e) {
            logger.error("[{}] Critical error in AnomalyDetectionJob: {}", jobId, e.getMessage(), e);
        }
    }

    /**
     * Map anomaly score to severity level
     */
    private String mapSeverity(Double score) {
        if (score == null || score < 0.5)
            return "LOW";
        if (score < 0.7)
            return "MEDIUM";
        if (score < 0.85)
            return "HIGH";
        return "CRITICAL";
    }
}
