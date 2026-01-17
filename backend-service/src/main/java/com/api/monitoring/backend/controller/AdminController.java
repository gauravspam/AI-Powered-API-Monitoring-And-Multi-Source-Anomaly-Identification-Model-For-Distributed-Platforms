package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.job.AnomalyDetectionJob;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/admin")
@CrossOrigin(origins = "*")
public class AdminController {

    @Autowired
    private AnomalyDetectionJob anomalyDetectionJob;

    /**
     * Manually trigger anomaly detection job
     */
    @PostMapping("/trigger-anomaly-detection")
    public ResponseEntity<Map<String, Object>> triggerAnomalyDetection() {
        try {
            // Execute job
            anomalyDetectionJob.detectAnomalies();
            
            Map<String, Object> response = new HashMap<>();
            response.put("message", "Anomaly detection job triggered successfully");
            response.put("timestamp", LocalDateTime.now());
            response.put("status", "SUCCESS");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("message", "Failed to trigger anomaly detection");
            errorResponse.put("error", e.getMessage());
            errorResponse.put("timestamp", LocalDateTime.now());
            errorResponse.put("status", "ERROR");
            
            return ResponseEntity.status(500).body(errorResponse);
        }
    }

    /**
     * Get job execution status
     */
    @GetMapping("/job-status")
    public ResponseEntity<Map<String, Object>> getJobStatus() {
        Map<String, Object> status = new HashMap<>();
        status.put("lastRun", anomalyDetectionJob.getLastExecutionTime());
        status.put("successCount", anomalyDetectionJob.getSuccessCount());
        status.put("failureCount", anomalyDetectionJob.getFailureCount());
        status.put("status", anomalyDetectionJob.getStatus());
        status.put("timestamp", LocalDateTime.now());
        
        return ResponseEntity.ok(status);
    }

    /**
     * Get job statistics
     */
    @GetMapping("/job-stats")
    public ResponseEntity<Map<String, Object>> getJobStats() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("totalExecutions", anomalyDetectionJob.getSuccessCount() + anomalyDetectionJob.getFailureCount());
        stats.put("successCount", anomalyDetectionJob.getSuccessCount());
        stats.put("failureCount", anomalyDetectionJob.getFailureCount());
        stats.put("lastExecution", anomalyDetectionJob.getLastExecutionTime());
        stats.put("successRate", calculateSuccessRate(
            anomalyDetectionJob.getSuccessCount(),
            anomalyDetectionJob.getFailureCount()
        ));
        
        return ResponseEntity.ok(stats);
    }

    private double calculateSuccessRate(int successCount, int failureCount) {
        int total = successCount + failureCount;
        if (total == 0) return 0.0;
        return (double) successCount / total * 100.0;
    }
}
