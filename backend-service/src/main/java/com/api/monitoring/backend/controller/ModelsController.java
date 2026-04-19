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
            Map.ofEntries(
                Map.entry("id", 1),
                Map.entry("name", "MSIF-LSTM"),
                Map.entry("version", "1.0.0"),
                Map.entry("type", "LSTM"),
                Map.entry("status", "online"),
                Map.entry("latencyMs", 45),
                Map.entry("throughputPerSec", 220),
                Map.entry("accuracy", 94.2),
                Map.entry("f1Score", 0.921),
                Map.entry("precision", 0.936),
                Map.entry("recall", 0.907),
                Map.entry("confidenceDrift", -0.012),
                Map.entry("inferenceLast24h", 18420),
                Map.entry("lastRetrainAt", LocalDateTime.now().minusDays(3).toString())
            ),
            Map.ofEntries(
                Map.entry("id", 2),
                Map.entry("name", "PLE-GRU"),
                Map.entry("version", "1.0.0"),
                Map.entry("type", "GRU"),
                Map.entry("status", "online"),
                Map.entry("latencyMs", 38),
                Map.entry("throughputPerSec", 280),
                Map.entry("accuracy", 91.7),
                Map.entry("f1Score", 0.894),
                Map.entry("precision", 0.913),
                Map.entry("recall", 0.878),
                Map.entry("confidenceDrift", 0.004),
                Map.entry("inferenceLast24h", 22105),
                Map.entry("lastRetrainAt", LocalDateTime.now().minusDays(3).toString())
            ),
            Map.ofEntries(
                Map.entry("id", 3),
                Map.entry("name", "Hybrid Ensemble"),
                Map.entry("version", "1.0.0"),
                Map.entry("type", "Ensemble"),
                Map.entry("status", "online"),
                Map.entry("latencyMs", 82),
                Map.entry("throughputPerSec", 150),
                Map.entry("accuracy", 96.1),
                Map.entry("f1Score", 0.947),
                Map.entry("precision", 0.962),
                Map.entry("recall", 0.935),
                Map.entry("confidenceDrift", -0.005),
                Map.entry("inferenceLast24h", 15922),
                Map.entry("lastRetrainAt", LocalDateTime.now().minusDays(3).toString())
            )
        );

        return ResponseEntity.ok(models);
    }
}