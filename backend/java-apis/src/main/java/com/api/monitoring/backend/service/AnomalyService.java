// backend/java-apis/src/main/java/com/api/monitoring/backend/service/AnomalyService.java

package com.api.monitoring.backend.service;

import com.api.monitoring.backend.dto.AnomalyResponse;
import com.api.monitoring.backend.dto.LogEntryRequest;
import com.api.monitoring.backend.dto.StatisticsResponse;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

@Service
public class AnomalyService {

  public List<AnomalyResponse> getLatestAnomalies(int limit) {
    List<AnomalyResponse> anomalies = new ArrayList<>();

    for (int i = 0; i < Math.min(limit, 5); i++) {
      AnomalyResponse anomaly = new AnomalyResponse();
      anomaly.setId((long) (i + 1));
      anomaly.setApiName("/api/users");
      anomaly.setStage(i % 2 == 0 ? 1 : 2);
      anomaly.setModel("IsolationForest");
      anomaly.setAnomalyScore(0.85 + (i * 0.02));
      anomaly.setStage2Score(0.75);
      anomaly.setFinalAnomalyScore(0.80);
      anomaly.setStatus("DETECTED");
      anomaly.setSeverity(i % 2 == 0 ? "HIGH" : "MEDIUM");
      anomaly.setConfidence(0.92);
      anomaly.setTimestamp(LocalDateTime.now().minusMinutes(i * 5).toString());
      anomalies.add(anomaly);
    }

    return anomalies;
  }

  // For AnomalyController.detectAnomaly
  public AnomalyResponse detectAnomaly(LogEntryRequest logEntry) {
    AnomalyResponse response = new AnomalyResponse();
    response.setId(System.currentTimeMillis());
    response.setApiName(logEntry.getApiName());
    response.setStage(1);
    response.setModel("IsolationForest");
    response.setAnomalyScore(0.75);
    response.setStatus("DETECTED");
    response.setSeverity("MEDIUM");
    response.setConfidence(0.85);
    response.setTimestamp(LocalDateTime.now().toString());
    return response;
  }

  // For AnomalyController.detectBatchAnomalies
  public List<AnomalyResponse> detectBatchAnomalies(LogEntryRequest[] logEntries) {
    List<AnomalyResponse> responses = new ArrayList<>();
    for (LogEntryRequest entry : logEntries) {
      responses.add(detectAnomaly(entry));
    }
    return responses;
  }

  // For AnomalyController.getRecentAnomalies
  public List<AnomalyResponse> getRecentAnomalies(String apiName, int limit) {
    return getLatestAnomalies(limit);
  }

  // For AnomalyController.getAllRecentAnomalies
  public List<AnomalyResponse> getAllRecentAnomalies(int limit) {
    return getLatestAnomalies(limit);
  }

  // For AnomalyController.getStatistics
  public StatisticsResponse getStatistics(String apiName) {
    StatisticsResponse stats = new StatisticsResponse();
    stats.setApiName(apiName);
    stats.setTotalLogs(1000L);
    stats.setNormalCount(800L);
    stats.setSuspiciousCount(150L);
    stats.setAnomalyCount(50L);
    stats.setAvgAnomalyScore(0.65);
    stats.setPeakHour(14);
    stats.setLast24hAnomalies(30L);
    stats.setAlertsTriggered(5L);
    stats.setErrorRateTrend("DECREASING");
    return stats;
  }

  // For AnomalyController.getMonitoredApis
  public List<String> getMonitoredApis() {
    return Arrays.asList("/api/users", "/api/orders", "/api/products", "/api/payments");
  }

  // For AnomalyController.getActiveAlertsCount
  public long getActiveAlertsCount() {
    return 5L;
  }

  // For AnomalyController.acknowledgeAnomaly
  public boolean acknowledgeAnomaly(Long id) {
    return true;
  }
}
