package com.api.monitoring.backend.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;

@RestController
@RequestMapping("/api/predictions")
public class PredictionController {

    private static final AtomicReference<PredictionMetadata> latestPrediction = 
        new AtomicReference<>(new PredictionMetadata());

    @GetMapping("/latest")
    public ResponseEntity<Map<String, Object>> getLatestPrediction() {
        PredictionMetadata metadata = latestPrediction.get();
        return ResponseEntity.ok(metadata.toMap());
    }

    public static void updatePrediction(String predictionId, String severity, int alertCount) {
        latestPrediction.set(new PredictionMetadata(predictionId, severity, alertCount));
    }

    private static class PredictionMetadata {
        private String predictionId;
        private String predictionTime;
        private String severity;
        private int alertCount;

        public PredictionMetadata() {
            this.predictionId = null;
            this.predictionTime = null;
            this.severity = null;
            this.alertCount = 0;
        }

        public PredictionMetadata(String predictionId, String severity, int alertCount) {
            this.predictionId = predictionId;
            this.predictionTime = Instant.now().toString();
            this.severity = severity;
            this.alertCount = alertCount;
        }

        public Map<String, Object> toMap() {
            Map<String, Object> map = new HashMap<>();
            map.put("prediction_id", predictionId);
            map.put("prediction_time", predictionTime);
            map.put("severity", severity);
            map.put("alert_count", alertCount);
            return map;
        }
    }
}