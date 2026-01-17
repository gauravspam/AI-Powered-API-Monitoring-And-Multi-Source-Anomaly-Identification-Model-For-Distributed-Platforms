package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.job.AnomalyDetectionJob;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/admin")
public class AdminController {

    private final AnomalyDetectionJob anomalyDetectionJob;

    public AdminController(AnomalyDetectionJob anomalyDetectionJob) {
        this.anomalyDetectionJob = anomalyDetectionJob;
    }

    /**
     * Manually trigger anomaly detection job (for testing)
     * POST http://localhost:8080/api/admin/trigger-job
     */
    @PostMapping("/trigger-job")
    public ResponseEntity<String> triggerJob() {
        try {
            anomalyDetectionJob.processRecentMetrics();
            return ResponseEntity.ok("Job triggered successfully");
        } catch (Exception e) {
            return ResponseEntity.status(500).body("Job failed: " + e.getMessage());
        }
    }
}
