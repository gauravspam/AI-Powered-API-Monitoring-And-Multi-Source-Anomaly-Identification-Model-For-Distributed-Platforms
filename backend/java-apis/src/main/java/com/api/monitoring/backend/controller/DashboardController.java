// backend/java-apis/src/main/java/com/api/monitoring/backend/controller/DashboardController.java

package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.dto.*;
import com.api.monitoring.backend.service.AnomalyService;
import com.api.monitoring.backend.service.OpenSearchLogService;
import com.api.monitoring.backend.service.OverviewService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.ArrayList;

@RestController
@RequestMapping("/api/dashboard")
@CrossOrigin(origins = "http://localhost:3000", allowedHeaders = "*", methods = { RequestMethod.GET,
    RequestMethod.POST })
public class DashboardController {

  @Autowired
  private AnomalyService anomalyService;

  @Autowired
  private OpenSearchLogService logService;

  @Autowired
  private OverviewService overviewService;

  // 1. GET /api/dashboard/kpi
  @GetMapping("/kpi")
  public ResponseEntity<?> getKpi() {
    try {
      MetricsDTO kpi = new MetricsDTO();
      kpi.setTotalRequests(logService.getTotalRequests());
      kpi.setSuccessRate(logService.getSuccessRate());
      kpi.setErrorRate(logService.getErrorRate());
      kpi.setAvgLatency(logService.getAvgLatency());
      kpi.setP95Latency(logService.getP95Latency());
      kpi.setP99Latency(logService.getP99Latency());
      kpi.setUptime(99.9);
      return ResponseEntity.ok(kpi);
    } catch (Exception e) {
      return ResponseEntity.status(500).body("Error: " + e.getMessage());
    }
  }

  // 2. GET /api/dashboard/env-summary
  @GetMapping("/env-summary")
  public ResponseEntity<?> getEnvironmentSummary() {
    try {
      return ResponseEntity.ok(overviewService.getEnvironmentSummary());
    } catch (Exception e) {
      return ResponseEntity.status(500).body("Error: " + e.getMessage());
    }
  }

  // 3. GET /api/dashboard/anomalies
  @GetMapping("/anomalies")
  public ResponseEntity<List<AnomalyResponse>> getAnomalies() { // ← Generic List
    try {
      List<AnomalyResponse> anomalies = anomalyService.getLatestAnomalies(20);
      return ResponseEntity.ok(anomalies); // ← Always returns array
    } catch (Exception e) {
      // Return empty array on error instead of null
      return ResponseEntity.ok(new ArrayList<>());
    }
  }

  // 4. GET /api/dashboard/traffic
  @GetMapping("/traffic")
  public ResponseEntity<?> getTraffic() {
    try {
      return ResponseEntity.ok(logService.getTrafficMetrics());
    } catch (Exception e) {
      return ResponseEntity.status(500).body("Error: " + e.getMessage());
    }
  }

  // 5. GET /api/dashboard (full dashboard - convenience endpoint)
  @GetMapping
  public ResponseEntity<?> getDashboard() {
    try {
      DashboardDTO dashboard = new DashboardDTO();

      // Create KPI directly instead of using getKpi().getBody()
      MetricsDTO kpi = new MetricsDTO();
      kpi.setTotalRequests(logService.getTotalRequests());
      kpi.setSuccessRate(logService.getSuccessRate());
      kpi.setErrorRate(logService.getErrorRate());
      kpi.setAvgLatency(logService.getAvgLatency());
      kpi.setP95Latency(logService.getP95Latency());
      kpi.setP99Latency(logService.getP99Latency());
      kpi.setUptime(99.9);

      dashboard.setKpi(kpi);
      dashboard.setAnomalies(anomalyService.getLatestAnomalies(20));
      dashboard.setEnvironment(overviewService.getEnvironmentSummary());
      dashboard.setTraffic(logService.getTrafficMetrics());
      dashboard.setTimestamp(LocalDateTime.now().toString());

      return ResponseEntity.ok(dashboard);
    } catch (Exception e) {
      return ResponseEntity.status(500).body("Error: " + e.getMessage());
    }
  }
}
