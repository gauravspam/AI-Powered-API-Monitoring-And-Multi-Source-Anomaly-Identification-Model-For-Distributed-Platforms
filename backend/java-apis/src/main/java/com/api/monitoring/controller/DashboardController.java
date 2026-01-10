package com.api.monitoring.controller;

import org.springframework.web.bind.annotation.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/api/v1/dashboard")
@CrossOrigin(origins = {"http://localhost:3000", "http://localhost:3001"})
public class DashboardController {
    private static final Logger log = LoggerFactory.getLogger(DashboardController.class);

    @GetMapping("/health")
    public Map<String, String> health() {
        Map<String, String> response = new HashMap<>();
        response.put("status", "OK");
        response.put("service", "api-monitoring-dashboard");
        return response;
    }

    @GetMapping("/summary")
    public Map<String, Object> summary() {
        Map<String, Object> summary = new HashMap<>();
        summary.put("totalAnomaliesLast24h", 0);
        summary.put("criticalCount", 0);
        summary.put("highCount", 0);
        summary.put("avgResponseTime", 145.5);
        return summary;
    }

    @PostMapping("/test-anomaly")
    public Map<String, Object> testAnomaly() {
        double fakeScore = 0.7 + Math.random() * 0.3;
        Map<String, Object> response = new HashMap<>();
        response.put("id", "test-123");
        response.put("score", fakeScore);
        response.put("severity", fakeScore > 0.8 ? "HIGH" : "MEDIUM");
        log.info("TEST ANOMALY generated: score={}, endpoint=/api/v1/orders", fakeScore);
        return response;
    }
}
