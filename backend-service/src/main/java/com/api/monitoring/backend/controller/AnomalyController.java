package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.model.AnomalyRecord;
import com.api.monitoring.backend.model.LogRecord;
import com.api.monitoring.backend.service.AnomalyService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/anomalies")
@Slf4j
public class AnomalyController {

    private final AnomalyService anomalyService;

    @Autowired
    public AnomalyController(AnomalyService anomalyService) {
        this.anomalyService = anomalyService;
    }

    @PostMapping("/analyze")
    public ResponseEntity<AnomalyRecord> analyzeLog(@RequestBody LogRecord logRecord) {
        try {
            log.info("📥 Received request to analyze log: {}", logRecord.getEndpoint());
            
            AnomalyRecord anomaly = anomalyService.analyzeApiLog(logRecord);
            
            log.info("✅ Analysis complete: anomaly_id={}, severity={}", 
                    anomaly.getId(), anomaly.getSeverity());
            
            return ResponseEntity.ok(anomaly);
            
        } catch (Exception e) {
            log.error("❌ Error analyzing log: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/recent")
    public ResponseEntity<List<AnomalyRecord>> getRecentAnomalies(
            @RequestParam(defaultValue = "60") int minutes) {
        try {
            List<AnomalyRecord> anomalies = anomalyService.getRecentAnomalies(minutes);
            return ResponseEntity.ok(anomalies);
        } catch (Exception e) {
            log.error("Error fetching recent anomalies: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/severity/{severity}")
    public ResponseEntity<List<AnomalyRecord>> getAnomaliesBySeverity(
            @PathVariable String severity) {
        try {
            List<AnomalyRecord> anomalies = anomalyService.getAnomaliesBySeverity(severity);
            return ResponseEntity.ok(anomalies);
        } catch (Exception e) {
            log.error("Error fetching anomalies by severity: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/critical")
    public ResponseEntity<List<AnomalyRecord>> getCriticalAnomalies(
            @RequestParam(defaultValue = "10") int limit) {
        try {
            List<AnomalyRecord> anomalies = anomalyService.getCriticalAnomalies(limit);
            return ResponseEntity.ok(anomalies);
        } catch (Exception e) {
            log.error("Error fetching critical anomalies: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/unacknowledged")
    public ResponseEntity<List<AnomalyRecord>> getUnacknowledgedCritical() {
        try {
            List<AnomalyRecord> anomalies = anomalyService.getUnacknowledgedCritical();
            return ResponseEntity.ok(anomalies);
        } catch (Exception e) {
            log.error("Error fetching unacknowledged anomalies: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @PostMapping("/{id}/acknowledge")
    public ResponseEntity<AnomalyRecord> acknowledgeAnomaly(
            @PathVariable Long id,
            @RequestParam String username) {
        try {
            AnomalyRecord anomaly = anomalyService.acknowledgeAnomaly(id, username);
            return ResponseEntity.ok(anomaly);
        } catch (Exception e) {
            log.error("Error acknowledging anomaly {}: {}", id, e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @PostMapping("/{id}/resolve")
    public ResponseEntity<AnomalyRecord> resolveAnomaly(@PathVariable Long id) {
        try {
            AnomalyRecord anomaly = anomalyService.resolveAnomaly(id);
            return ResponseEntity.ok(anomaly);
        } catch (Exception e) {
            log.error("Error resolving anomaly {}: {}", id, e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/stats")
    public ResponseEntity<Map<String, Long>> getAnomalyStatistics(
            @RequestParam(defaultValue = "24") int hours) {
        try {
            Map<String, Long> stats = anomalyService.getAnomalyStatistics(hours);
            return ResponseEntity.ok(stats);
        } catch (Exception e) {
            log.error("Error fetching anomaly statistics: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}
