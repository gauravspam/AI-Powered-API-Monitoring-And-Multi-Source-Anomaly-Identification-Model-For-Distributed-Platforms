package com.api.monitoring.backend;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
public class ApiController {

    @GetMapping("/")
    public Map<String, String> home() {
        return Map.of("message", "API Monitoring Backend is running");
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "UP");
    }

    @GetMapping("/api/overview")
    public Map<String, Object> overview() {
        return Map.of(
            "totalRequests", 124500,
            "errorRate", 0.8,
            "anomaliesLast24h", 12,
            "avgLatencyMs", 180
        );
    }

    @GetMapping("/api/anomalies")
    public List<Map<String, Object>> anomalies() {
        return List.of(
            Map.of(
                "id", "a1",
                "service", "payments-api",
                "environment", "prod",
                "severity", "high",
                "timestamp", "2025-12-20T10:15:00Z",
                "message", "Spike in 5xx errors",
                "score", 0.96
            )
        );
    }
}