package com.api.monitoring.backend.service;

import org.springframework.stereotype.Service;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
public class AnomalyService {

    public List<Map<String, Object>> getRecentErrorAnomalies() throws IOException {
        List<Map<String, Object>> anomalies = new ArrayList<>();

        Map<String, Object> a = Map.of(
            "service", "demo-service",
            "level", "INFO",
            "message", "Test log from Spring Boot",
            "timestamp", 1766239768858L
        );
        anomalies.add(a);

        return anomalies;
    }
}
