package com.api.monitoring.backend;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
public class HealthController {

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "UP");
    }

    @GetMapping("/api/anomalies/sample")
    public List<Map<String, Object>> sampleAnomalies() {
        return List.of(
                Map.of(
                        "id", "a1",
                        "service", "payments-api",
                        "environment", "prod",
                        "severity", "high",
                        "timestamp", "2025-12-20T10:15:00Z",
                        "message", "Spike in 5xx errors",
                        "score", 0.96
                ),
                Map.of(
                        "id", "a2",
                        "service", "search-api",
                        "environment", "staging",
                        "severity", "medium",
                        "timestamp", "2025-12-20T11:00:00Z",
                        "message", "Latency above 95th percentile",
                        "score", 0.78
                )
        );
    }
}
