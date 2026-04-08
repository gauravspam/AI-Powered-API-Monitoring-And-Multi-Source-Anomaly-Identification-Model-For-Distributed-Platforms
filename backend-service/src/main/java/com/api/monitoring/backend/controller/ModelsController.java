package com.api.monitoring.backend.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class ModelsController {

    @GetMapping("/models")
    public ResponseEntity<List<Map<String, Object>>> getModels() {
        List<Map<String, Object>> models = Arrays.asList(
            Map.of(
                "id", 1,
                "name", "MSIF-LSTM",
                "version", "1.0.0",
                "type", "LSTM",
                "status", "online",
                "latencyMs", 45,
                "throughputPerSec", 220,
                "accuracy", 94.2,
                "lastRetrainAt", LocalDateTime.now().minusDays(3).toString()
            ),
            Map.of(
                "id", 2,
                "name", "PLE-GRU",
                "version", "1.0.0",
                "type", "GRU",
                "status", "online",
                "latencyMs", 38,
                "throughputPerSec", 280,
                "accuracy", 91.7,
                "lastRetrainAt", LocalDateTime.now().minusDays(3).toString()
            ),
            Map.of(
                "id", 3,
                "name", "Hybrid Ensemble",
                "version", "1.0.0",
                "type", "Ensemble",
                "status", "online",
                "latencyMs", 82,
                "throughputPerSec", 150,
                "accuracy", 96.1,
                "lastRetrainAt", LocalDateTime.now().minusDays(3).toString()
            )
        );

        return ResponseEntity.ok(models);
    }
}