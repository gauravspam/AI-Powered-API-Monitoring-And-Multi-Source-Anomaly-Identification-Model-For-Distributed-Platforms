package com.api.monitoring.backend.service;

import com.api.monitoring.backend.dto.AnomalyResponse;
import com.api.monitoring.backend.dto.AnomalyScoresResponse;
import com.api.monitoring.backend.dto.FeatureWindow;
import com.api.monitoring.backend.dto.LogEntryRequest;
import com.api.monitoring.backend.dto.StatisticsResponse;
import com.api.monitoring.backend.model.AnomalyRecord;
import com.api.monitoring.backend.model.MetricRecord;
import com.api.monitoring.backend.repository.AnomalyRepository;
import com.api.monitoring.backend.repository.MetricRepository;
import com.api.monitoring.backend.util.FeatureEngineer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class AnomalyService {

    private static final Logger logger = LoggerFactory.getLogger(AnomalyService.class);

    @Autowired
    private AnomalyRepository anomalyRepository;

    @Autowired
    private MetricRepository metricRepository;

    @Autowired
    private PythonMLService pythonMLService;

    @Autowired
    private FeatureEngineer featureEngineer;

    public List<AnomalyResponse> getRecentAnomalies(int limit) {
        logger.info("Fetching recent {} anomalies", limit);
        List<AnomalyRecord> anomalies = anomalyRepository.findTop10ByOrderByTimestampDesc();
        return anomalies.stream()
                .limit(limit)
                .map(this::convertToResponse)
                .collect(Collectors.toList());
    }

    public void detectAndSaveAnomalies() {
        logger.info("Starting anomaly detection for all APIs...");
        
        try {
            List<Long> apiIds = metricRepository.findDistinctApiIds();
            logger.info("Found {} unique API IDs to process", apiIds.size());
            
            for (Long apiId : apiIds) {
                detectAndSaveAnomalyForApi(apiId);
            }
            
            logger.info("Anomaly detection completed for all APIs");
            
        } catch (Exception e) {
            logger.error("Error in anomaly detection: {}", e.getMessage(), e);
            throw e;
        }
    }

    private void detectAndSaveAnomalyForApi(Long apiId) {
        String traceId = "trace_" + apiId + "_" + System.currentTimeMillis();
        
        try {
            String apiName = "api_" + apiId;
            logger.info("[{}] Processing anomaly detection for API: {}", traceId, apiName);
            
            LocalDateTime twentyFourHoursAgo = LocalDateTime.now().minusHours(24);
            List<MetricRecord> metrics = metricRepository.findByApiIdAndTimestampAfter(apiId, twentyFourHoursAgo);
            
            if (metrics.isEmpty()) {
                logger.warn("[{}] No metrics found for API {}", traceId, apiName);
                return;
            }
            
            logger.info("[{}] Found {} metrics for API {}", traceId, metrics.size(), apiName);
            
            List<Double[]> msifFeatures = featureEngineer.buildMsifFeatures(metrics);
            logger.info("[{}] Built MSIF features: {} timesteps", traceId, msifFeatures.size());
            
            List<Double[]> pleFeatures = featureEngineer.buildPleFeatures(metrics, LocalDateTime.now());
            logger.info("[{}] Built PLE features: {} timesteps", traceId, pleFeatures.size());
            
            FeatureWindow featureWindow = new FeatureWindow();
            featureWindow.setEndpoint(apiName);
            featureWindow.setMethod("AGGREGATE");
            featureWindow.setMsifFeatures(msifFeatures);
            featureWindow.setPleFeatures(pleFeatures);
            featureWindow.setWindowSizeMins(1440);
            featureWindow.setStartTimestamp(System.currentTimeMillis() - (24 * 60 * 60 * 1000L));
            featureWindow.setEndTimestamp(System.currentTimeMillis());
            
            logger.info("[{}] Calling ML service...", traceId);
            AnomalyScoresResponse mlResponse = pythonMLService.predictWithFeatures(featureWindow, traceId);
            
            if (mlResponse != null) {
                saveAnomalyWithMLScores(apiName, mlResponse, traceId);
            } else {
                logger.warn("[{}] ML service returned null", traceId);
            }
            
        } catch (Exception e) {
            logger.error("[{}] Error processing API {}: {}", traceId, apiId, e.getMessage(), e);
        }
    }

    private void saveAnomalyWithMLScores(String apiName, AnomalyScoresResponse mlResponse, String traceId) {
        AnomalyRecord anomaly = new AnomalyRecord();
        anomaly.setApiName(apiName);
        anomaly.setTimestamp(LocalDateTime.now());
        
        Double msifScore = mlResponse.getMsifLstmScore() != null ? mlResponse.getMsifLstmScore() : 0.0;
        Double pleScore = mlResponse.getPleGruScore() != null ? mlResponse.getPleGruScore() : 0.0;
        Double hybridScore = mlResponse.getHybridScore() != null ? mlResponse.getHybridScore() : 0.0;
        Double confidence = mlResponse.getConfidence() != null ? mlResponse.getConfidence() : 0.0;
        
        anomaly.setMsifLstmScore(msifScore);
        anomaly.setPleGruScore(pleScore);
        anomaly.setHybridScore(hybridScore);
        anomaly.setFinalAnomalyScore(hybridScore);
        anomaly.setConfidence(confidence);
        
        if (hybridScore >= 0.7) {
            anomaly.setSeverity("HIGH");
        } else if (hybridScore >= 0.5) {
            anomaly.setSeverity("MEDIUM");
        } else {
            anomaly.setSeverity("LOW");
        }
        
        anomaly.setStatus("ACTIVE");
        anomaly.setMlModelUsed("MSIF-LSTM + PLE-GRU Hybrid");
        
        anomalyRepository.save(anomaly);
        logger.info("[{}] Anomaly saved: MSIF={} PLE={} Hybrid={}", 
            traceId, msifScore, pleScore, hybridScore);
    }

    public AnomalyResponse detectAnomaly(LogEntryRequest logEntry) {
        AnomalyResponse response = new AnomalyResponse();
        response.setApiName(logEntry.getApiName());
        response.setFinalAnomalyScore(0.5);
        response.setSeverity("MEDIUM");
        response.setConfidence(0.7);
        response.setStatus("DETECTED");
        response.setTimestamp(LocalDateTime.now().toString());
        return response;
    }

    public List<AnomalyResponse> detectBatchAnomalies(LogEntryRequest[] logEntries) {
        List<AnomalyResponse> responses = new ArrayList<>();
        for (LogEntryRequest entry : logEntries) {
            responses.add(detectAnomaly(entry));
        }
        return responses;
    }

    public List<AnomalyResponse> getRecentAnomalies(String apiName, int limit) {
        logger.info("Fetching {} anomalies for API: {}", limit, apiName);
        List<AnomalyRecord> anomalies = anomalyRepository.findTop100ByApiNameOrderByTimestampDesc(apiName);
        return anomalies.stream()
                .limit(limit)
                .map(this::convertToResponse)
                .collect(Collectors.toList());
    }

    public List<AnomalyResponse> getAllRecentAnomalies(int limit) {
        return getRecentAnomalies(limit);
    }

    public List<AnomalyResponse> getLatestAnomalies(int limit) {
        return getRecentAnomalies(limit);
    }

    public StatisticsResponse getStatistics(String apiName) {
        StatisticsResponse stats = new StatisticsResponse();
        stats.setApiName(apiName);
        
        List<AnomalyRecord> anomalies = anomalyRepository.findByApiName(apiName);
        stats.setAnomalyCount((long) anomalies.size());
        
        double avgScore = anomalies.stream()
                .mapToDouble(AnomalyRecord::getFinalAnomalyScore)
                .average()
                .orElse(0.0);
        stats.setAvgAnomalyScore(avgScore);
        
        long normalCount = anomalies.stream().filter(a -> "LOW".equals(a.getSeverity())).count();
        long suspiciousCount = anomalies.stream().filter(a -> "MEDIUM".equals(a.getSeverity())).count();
        long anomalyCount = anomalies.stream().filter(a -> "HIGH".equals(a.getSeverity())).count();
        
        stats.setNormalCount(normalCount);
        stats.setSuspiciousCount(suspiciousCount);
        stats.setAnomalyCount(anomalyCount);
        stats.setTotalLogs((long) anomalies.size());
        stats.setLast24hAnomalies((long) anomalies.size());
        stats.setAlertsTriggered(0L);
        stats.setErrorRateTrend("STABLE");
        
        return stats;
    }

    public List<String> getMonitoredApis() {
        List<Long> apiIds = metricRepository.findDistinctApiIds();
        return apiIds.stream()
                .map(id -> "api_" + id)
                .collect(Collectors.toList());
    }

    public long getActiveAlertsCount() {
        return anomalyRepository.findAll().stream()
                .filter(a -> "ACTIVE".equals(a.getStatus()))
                .count();
    }

    public boolean acknowledgeAnomaly(Long id) {
        try {
            AnomalyRecord anomaly = anomalyRepository.findById(id).orElse(null);
            if (anomaly != null) {
                anomaly.setAcknowledged(true);
                anomaly.setStatus("ACKNOWLEDGED");
                anomalyRepository.save(anomaly);
                return true;
            }
            return false;
        } catch (Exception e) {
            logger.error("Error acknowledging anomaly {}: {}", id, e.getMessage());
            return false;
        }
    }

    private AnomalyResponse convertToResponse(AnomalyRecord record) {
        AnomalyResponse response = new AnomalyResponse();
        response.setId(record.getId());
        response.setApiName(record.getApiName());
        response.setSeverity(record.getSeverity());
        response.setFinalAnomalyScore(record.getFinalAnomalyScore());
        response.setConfidence(record.getConfidence());
        response.setStatus(record.getStatus());
        response.setTimestamp(record.getTimestamp().toString());
        return response;
    }
}
