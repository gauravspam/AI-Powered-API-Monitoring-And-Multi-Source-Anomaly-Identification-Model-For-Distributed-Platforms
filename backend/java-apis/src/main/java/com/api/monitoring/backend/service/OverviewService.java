package com.api.monitoring.backend.service;

import com.api.monitoring.backend.dto.EnvironmentSummaryDTO; // ← ADD THIS
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Service
public class OverviewService {

  @Autowired
  private OpenSearchLogService openSearchLogService;

  public Map<String, Object> getOverview() {
    Map<String, Object> overview = new HashMap<>();
    overview.put("totalServices", 5);
    overview.put("healthyServices", 4);
    overview.put("totalEndpoints", 20);
    overview.put("avgResponseTime", 150.0);
    overview.put("uptime", 99.5);
    return overview;
  }

  public EnvironmentSummaryDTO getEnvironmentSummary() {
    EnvironmentSummaryDTO summary = new EnvironmentSummaryDTO();
    summary.setTotalServices(5);
    summary.setHealthyServices(4);
    summary.setTotalEndpoints(20);
    summary.setAvgResponseTime(150.0);
    summary.setDeployments(3);
    summary.setUptimePercentage(99.5);
    return summary;
  }

  private int countDistinctServices() {
    return 5; // Placeholder
  }

  private int countHealthyServices() {
    return 4; // Placeholder
  }

  private int countDistinctEndpoints() {
    return 20; // Placeholder
  }

  private double getAverageResponseTime() {
    return 150.0; // Placeholder
  }
}
