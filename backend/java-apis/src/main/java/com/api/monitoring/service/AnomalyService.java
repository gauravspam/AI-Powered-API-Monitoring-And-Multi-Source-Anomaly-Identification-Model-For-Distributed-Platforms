package com.api.monitoring.service;

import com.api.monitoring.entity.AnomalyScore;
import com.api.monitoring.repository.AnomalyScoreRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Service for anomaly detection and management
 */
@Service
@Slf4j
public class AnomalyService {
    
    @Autowired
    private AnomalyScoreRepository anomalyScoreRepository;
    
    @Autowired
    private LoggingService loggingService;
    
    /**
     * Save anomaly score to database and log it
     */
    public AnomalyScore saveAnomalyScore(String endpoint, 
                                         String anomalyType, 
                                         double score) {
        return saveAnomalyScore(endpoint, "GET", anomalyType, score);
    }
    
    /**
     * Save anomaly score with HTTP method
     */
    public AnomalyScore saveAnomalyScore(String endpoint, 
                                         String method,
                                         String anomalyType, 
                                         double score) {
        try {
            AnomalyScore anomaly = new AnomalyScore();
            anomaly.setApiEndpoint(endpoint);
            anomaly.setMethod(method);
            anomaly.setAnomalyType(anomalyType);
            anomaly.setScore((float) score);
            
            AnomalyScore saved = anomalyScoreRepository.save(anomaly);
            
            log.info("Anomaly saved: {} - {} (score: {})",
                endpoint, anomalyType, score);
            
            Map<String, Object> metadata = new HashMap<>();
            metadata.put("api_endpoint", endpoint);
            metadata.put("method", method);
            metadata.put("database_id", saved.getId());
            
            loggingService.logAnomaly(
                anomalyType, 
                score, 
                endpoint,
                metadata
            );
            
            return saved;
            
        } catch (Exception e) {
            log.error("Failed to save anomaly score", e);
            throw new RuntimeException("Failed to save anomaly score", e);
        }
    }
    
    /**
     * Get latest anomalies across all endpoints
     */
    public List<AnomalyScore> getLatestAnomalies(int limit) {
        Pageable pageable = PageRequest.of(0, limit);
        LocalDateTime lastDay = LocalDateTime.now().minusHours(24);
        
        return anomalyScoreRepository.findHighestScoresAfter(
            lastDay,
            pageable
        );
    }
    
    /**
     * Get anomalies for a specific endpoint
     */
    public List<AnomalyScore> getAnomaliesForEndpoint(String endpoint, int limit) {
        Pageable pageable = PageRequest.of(0, limit);
        return anomalyScoreRepository.findByApiEndpointOrderByTimestampDesc(
            endpoint,
            pageable
        );
    }
    
    /**
     * Get anomalies by type
     */
    public List<AnomalyScore> getAnomaliesByType(String anomalyType, int limit) {
        Pageable pageable = PageRequest.of(0, limit);
        return anomalyScoreRepository.findByAnomalyTypeOrderByTimestampDesc(
            anomalyType,
            pageable
        );
    }
    
    /**
     * Get high-severity anomalies
     */
    public List<AnomalyScore> getHighSeverityAnomalies(int limit) {
        Pageable pageable = PageRequest.of(0, limit);
        return anomalyScoreRepository.findBySeverityOrderByTimestampDesc(
            "HIGH",
            pageable
        );
    }
    
    /**
     * Get critical anomalies
     */
    public List<AnomalyScore> getCriticalAnomalies(int limit) {
        Pageable pageable = PageRequest.of(0, limit);
        return anomalyScoreRepository.findBySeverityOrderByTimestampDesc(
            "CRITICAL",
            pageable
        );
    }
    
    /**
     * Count anomalies by severity level in last 24 hours
     */
    public long countAnomaliesBySeverity(String severity) {
        LocalDateTime lastDay = LocalDateTime.now().minusHours(24);
        return anomalyScoreRepository.countBySeverityAndTimeRange(
            severity,
            lastDay
        );
    }
    
    /**
     * Get anomaly statistics for dashboard
     */
    public Map<String, Object> getAnomalyStats() {
        LocalDateTime lastDay = LocalDateTime.now().minusHours(24);
        long totalAnomalies = anomalyScoreRepository.countSince(lastDay);
        long criticalCount = countAnomaliesBySeverity("CRITICAL");
        long highCount = countAnomaliesBySeverity("HIGH");
        long mediumCount = countAnomaliesBySeverity("MEDIUM");
        
        Map<String, Object> stats = new HashMap<>();
        stats.put("total_last_24h", totalAnomalies);
        stats.put("critical_count", criticalCount);
        stats.put("high_count", highCount);
        stats.put("medium_count", mediumCount);
        stats.put("latest_anomalies", getLatestAnomalies(10));
        stats.put("latest_critical", getCriticalAnomalies(5));
        
        return stats;
    }
}
