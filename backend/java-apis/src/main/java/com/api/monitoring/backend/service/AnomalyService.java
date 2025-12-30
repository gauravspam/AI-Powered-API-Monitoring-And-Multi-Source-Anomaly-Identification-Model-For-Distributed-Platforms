package com.api.monitoring.backend.service;

import com.api.monitoring.backend.dto.AnomalyResponse;
import com.api.monitoring.backend.dto.LogEntryRequest;
import com.api.monitoring.backend.dto.StatisticsResponse;
import com.api.monitoring.backend.model.AnomalyRecord;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

@Service
public class AnomalyService {

    private final PythonMLService pythonMLService;
    
    // In-memory storage (in production, use database)
    private final Map<Long, AnomalyRecord> anomalyStorage = new ConcurrentHashMap<>();
    private final List<AnomalyRecord> anomalyList = Collections.synchronizedList(new ArrayList<>());

    public AnomalyService(PythonMLService pythonMLService) {
        this.pythonMLService = pythonMLService;
    }

    /**
     * Detect anomaly for a single log entry
     */
    public AnomalyResponse detectAnomaly(LogEntryRequest logEntry) {
        // Call Python ML service
        AnomalyResponse response = pythonMLService.detectAnomaly(logEntry);
        
        // Store the anomaly record
        AnomalyRecord record = convertToRecord(response);
        anomalyList.add(record);
        anomalyStorage.put(record.getId(), record);
        
        return response;
    }

    /**
     * Detect anomalies for batch of log entries
     */
    public List<AnomalyResponse> detectBatchAnomalies(LogEntryRequest[] logEntries) {
        // Call Python ML service
        AnomalyResponse[] responses = pythonMLService.detectBatchAnomalies(logEntries);
        
        // Store all anomaly records
        List<AnomalyResponse> resultList = new ArrayList<>();
        for (AnomalyResponse response : responses) {
            AnomalyRecord record = convertToRecord(response);
            anomalyList.add(record);
            anomalyStorage.put(record.getId(), record);
            resultList.add(response);
        }
        
        return resultList;
    }

    /**
     * Get recent anomalies for a specific API
     */
    public List<AnomalyResponse> getRecentAnomalies(String apiName, int limit) {
        return anomalyList.stream()
                .filter(record -> apiName == null || apiName.equals(record.getApiName()))
                .filter(record -> !record.getAcknowledged())
                .sorted((a, b) -> b.getTimestamp().compareTo(a.getTimestamp()))
                .limit(limit)
                .map(this::convertToResponse)
                .collect(Collectors.toList());
    }

    /**
     * Get all recent anomalies across all APIs
     */
    public List<AnomalyResponse> getAllRecentAnomalies(int limit) {
        return getRecentAnomalies(null, limit);
    }

    /**
     * Get statistics for a specific API
     */
    public StatisticsResponse getStatistics(String apiName) {
        List<AnomalyRecord> apiRecords = anomalyList.stream()
                .filter(record -> apiName.equals(record.getApiName()))
                .collect(Collectors.toList());

        StatisticsResponse stats = new StatisticsResponse();
        stats.setApiName(apiName);
        stats.setTotalLogs((long) apiRecords.size());
        
        long normalCount = apiRecords.stream()
                .filter(r -> "NORMAL".equals(r.getStatus()))
                .count();
        long suspiciousCount = apiRecords.stream()
                .filter(r -> "SUSPICIOUS".equals(r.getStatus()))
                .count();
        long anomalyCount = apiRecords.stream()
                .filter(r -> "ANOMALY_DETECTED".equals(r.getStatus()))
                .count();
        
        stats.setNormalCount(normalCount);
        stats.setSuspiciousCount(suspiciousCount);
        stats.setAnomalyCount(anomalyCount);
        
        // Calculate average anomaly score
        OptionalDouble avgScore = apiRecords.stream()
                .mapToDouble(r -> r.getFinalAnomalyScore() != null ? r.getFinalAnomalyScore() : 0.0)
                .average();
        stats.setAvgAnomalyScore(avgScore.isPresent() ? avgScore.getAsDouble() : 0.0);
        
        // Find peak hour (hour with most anomalies)
        Map<Integer, Long> hourCounts = apiRecords.stream()
                .filter(r -> "ANOMALY_DETECTED".equals(r.getStatus()))
                .collect(Collectors.groupingBy(
                        r -> r.getTimestamp().getHour(),
                        Collectors.counting()
                ));
        Optional<Map.Entry<Integer, Long>> peakHourEntry = hourCounts.entrySet().stream()
                .max(Map.Entry.comparingByValue());
        stats.setPeakHour(peakHourEntry.map(Map.Entry::getKey).orElse(null));
        
        // Count anomalies in last 24 hours
        LocalDateTime last24h = LocalDateTime.now().minus(24, ChronoUnit.HOURS);
        long last24hAnomalies = apiRecords.stream()
                .filter(r -> "ANOMALY_DETECTED".equals(r.getStatus()))
                .filter(r -> r.getTimestamp().isAfter(last24h))
                .count();
        stats.setLast24hAnomalies(last24hAnomalies);
        
        // Count alerts triggered (anomalies with HIGH or MEDIUM severity)
        long alertsTriggered = apiRecords.stream()
                .filter(r -> "ANOMALY_DETECTED".equals(r.getStatus()))
                .filter(r -> "HIGH".equals(r.getSeverity()) || "MEDIUM".equals(r.getSeverity()))
                .count();
        stats.setAlertsTriggered(alertsTriggered);
        
        // Simple trend calculation (comparing last 24h to previous 24h)
        LocalDateTime last48h = LocalDateTime.now().minus(48, ChronoUnit.HOURS);
        long previous24hAnomalies = apiRecords.stream()
                .filter(r -> "ANOMALY_DETECTED".equals(r.getStatus()))
                .filter(r -> r.getTimestamp().isAfter(last48h) && r.getTimestamp().isBefore(last24h))
                .count();
        
        if (last24hAnomalies > previous24hAnomalies) {
            stats.setErrorRateTrend("increasing");
        } else if (last24hAnomalies < previous24hAnomalies) {
            stats.setErrorRateTrend("decreasing");
        } else {
            stats.setErrorRateTrend("stable");
        }
        
        return stats;
    }

    /**
     * Acknowledge an anomaly (mark as handled)
     */
    public boolean acknowledgeAnomaly(Long id) {
        AnomalyRecord record = anomalyStorage.get(id);
        if (record != null) {
            record.setAcknowledged(true);
            return true;
        }
        return false;
    }

    /**
     * Get count of active alerts (unacknowledged anomalies)
     */
    public long getActiveAlertsCount() {
        return anomalyList.stream()
                .filter(r -> !r.getAcknowledged())
                .filter(r -> "ANOMALY_DETECTED".equals(r.getStatus()))
                .count();
    }

    /**
     * Get unique API names being monitored
     */
    public Set<String> getMonitoredApis() {
        return anomalyList.stream()
                .map(AnomalyRecord::getApiName)
                .filter(Objects::nonNull)
                .collect(Collectors.toSet());
    }

    /**
     * Convert AnomalyResponse to AnomalyRecord
     */
    private AnomalyRecord convertToRecord(AnomalyResponse response) {
        AnomalyRecord record = new AnomalyRecord();
        record.setApiName(response.getApiName());
        record.setStage(response.getStage());
        record.setModel(response.getModel());
        record.setAnomalyScore(response.getAnomalyScore());
        record.setStage2Score(response.getStage2Score());
        record.setFinalAnomalyScore(response.getFinalAnomalyScore());
        record.setStatus(response.getStatus());
        record.setSeverity(response.getSeverity());
        record.setConfidence(response.getConfidence());
        
        if (response.getTimestamp() != null) {
            try {
                record.setTimestamp(LocalDateTime.parse(response.getTimestamp().replace("Z", "")));
            } catch (Exception e) {
                record.setTimestamp(LocalDateTime.now());
            }
        } else {
            record.setTimestamp(LocalDateTime.now());
        }
        
        return record;
    }

    /**
     * Convert AnomalyRecord to AnomalyResponse
     */
    private AnomalyResponse convertToResponse(AnomalyRecord record) {
        AnomalyResponse response = new AnomalyResponse();
        response.setId(record.getId());
        response.setApiName(record.getApiName());
        response.setStage(record.getStage());
        response.setModel(record.getModel());
        response.setAnomalyScore(record.getAnomalyScore());
        response.setStage2Score(record.getStage2Score());
        response.setFinalAnomalyScore(record.getFinalAnomalyScore());
        response.setStatus(record.getStatus());
        response.setSeverity(record.getSeverity());
        response.setConfidence(record.getConfidence());
        response.setTimestamp(record.getTimestamp().toString());
        return response;
    }
}
