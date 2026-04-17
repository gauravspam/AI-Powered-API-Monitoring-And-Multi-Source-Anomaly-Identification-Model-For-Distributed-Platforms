package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.service.DashboardService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/dashboard")
public class DashboardController {

    @Autowired
    private DashboardService dashboardService;

    @GetMapping("/kpi")
    public ResponseEntity<Map<String, Object>> getKpi() {
        Map<String, Object> kpi = new HashMap<>();
        kpi.put("totalRequests", dashboardService.getTotalRequests());
        kpi.put("successRate", dashboardService.getSuccessRate());
        kpi.put("errorRate", dashboardService.getErrorRate());
        kpi.put("avgLatency", dashboardService.getAvgLatency());
        kpi.put("p95Latency", dashboardService.getP95Latency());
        kpi.put("p99Latency", dashboardService.getP99Latency());
        kpi.put("currentRPS", dashboardService.getCurrentRPS());
        kpi.put("peakRPS", dashboardService.getPeakRPS());
        kpi.put("averageRPS", dashboardService.getAverageRPS());
        kpi.put("activeServices", dashboardService.getActiveServices());
        kpi.put("anomalyCount", dashboardService.getAnomalyCount());
        kpi.put("alertCount", dashboardService.getAlertCount());
        kpi.put("timestamp", System.currentTimeMillis());
        return ResponseEntity.ok(kpi);
    }
}