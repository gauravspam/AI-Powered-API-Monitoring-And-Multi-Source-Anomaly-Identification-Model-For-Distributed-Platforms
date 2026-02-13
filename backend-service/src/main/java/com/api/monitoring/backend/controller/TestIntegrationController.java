package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.dto.ml.PredictionResponseDto;
import com.api.monitoring.backend.model.*;
import com.api.monitoring.backend.service.MLServiceClient;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.util.Collections;
import java.util.List;

@RestController
@RequestMapping("/api/test-ml")
@RequiredArgsConstructor
public class TestIntegrationController {

    private final MLServiceClient mlServiceClient;

    @PostMapping("/trigger")
    public ResponseEntity<?> triggerTest() {
        // 1. Create Dummy Data
        Instant now = Instant.now();
        Instant start = now.minusSeconds(60);

        MetricRecord metric = new MetricRecord();
        metric.setCpuUsagePercent(45.5);
        metric.setCreatedAt(java.time.LocalDateTime.now());

        LogRecord log = new LogRecord();
        log.setStatusCode(500);
        log.setEndpoint("GET /api/users");
        log.setCreatedAt(java.time.LocalDateTime.now());

        // 2. Call ML Service
        PredictionResponseDto response = mlServiceClient.detectAnomaly(
                List.of(metric),
                List.of(log),
                Collections.emptyList(), // no traces
                "test-service-integration",
                start,
                now);

        return ResponseEntity.ok(response);
    }
}
