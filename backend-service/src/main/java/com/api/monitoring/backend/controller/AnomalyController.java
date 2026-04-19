package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.dto.AnomalyResponse;
import com.api.monitoring.backend.dto.LogEntryRequest;
import com.api.monitoring.backend.dto.StatisticsResponse;
import com.api.monitoring.backend.model.AnomalyRecord;
import com.api.monitoring.backend.model.LogRecord; // Ensure this exists or use LogEntryRequest
import com.api.monitoring.backend.service.AnomalyService;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/anomalies")
@CrossOrigin(origins = "*")
@Slf4j
public class AnomalyController {

    private final AnomalyService anomalyService;

    @Autowired
    public AnomalyController(AnomalyService anomalyService) {
        this.anomalyService = anomalyService;
    }

    // --- Analysis Endpoints ---

    @PostMapping("/analyze")
    public ResponseEntity<AnomalyResponse> analyzeLog(
        @RequestBody LogEntryRequest logEntry
    ) {
        try {
            log.info(
                "📥 Received request to analyze log: {}",
                logEntry.getApiName()
            );

            // Map to Service Method
            AnomalyResponse response = anomalyService.detectAnomaly(logEntry);

            log.info(
                "✅ Analysis complete: severity={}",
                response.getSeverity()
            );
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("❌ Error analyzing log: {}", e.getMessage(), e);
            return ResponseEntity.status(
                HttpStatus.INTERNAL_SERVER_ERROR
            ).build();
        }
    }

    // --- Retrieval Endpoints ---

    @GetMapping("/recent")
    public ResponseEntity<List<AnomalyResponse>> getRecentAnomalies(
        @RequestParam(defaultValue = "10") int limit
    ) {
        // Changed 'minutes' to 'limit' to match service
        try {
            List<AnomalyResponse> anomalies = anomalyService.getRecentAnomalies(
                limit
            );
            return ResponseEntity.ok(anomalies);
        } catch (Exception e) {
            log.error("Error fetching recent anomalies: {}", e.getMessage());
            return ResponseEntity.status(
                HttpStatus.INTERNAL_SERVER_ERROR
            ).build();
        }
    }

    @GetMapping("/severity/{severity}")
    public ResponseEntity<List<AnomalyResponse>> getAnomaliesBySeverity(
        @PathVariable String severity
    ) {
        try {
            // Service doesn't have direct filter, so we filter here (or add method to service later)
            List<AnomalyResponse> all = anomalyService.getRecentAnomalies(100);
            List<AnomalyResponse> filtered = all
                .stream()
                .filter(a -> a.getSeverity().equalsIgnoreCase(severity))
                .collect(Collectors.toList());
            return ResponseEntity.ok(filtered);
        } catch (Exception e) {
            log.error(
                "Error fetching anomalies by severity: {}",
                e.getMessage()
            );
            return ResponseEntity.status(
                HttpStatus.INTERNAL_SERVER_ERROR
            ).build();
        }
    }

    @GetMapping("/critical")
    public ResponseEntity<List<AnomalyResponse>> getCriticalAnomalies(
        @RequestParam(defaultValue = "10") int limit
    ) {
        return getAnomaliesBySeverity("HIGH"); // Reuse logic
    }

    @GetMapping("/unacknowledged")
    public ResponseEntity<List<AnomalyResponse>> getUnacknowledgedCritical() {
        try {
            List<AnomalyResponse> all = anomalyService.getRecentAnomalies(100);
            List<AnomalyResponse> unack = all
                .stream()
                .filter(a -> !"ACKNOWLEDGED".equals(a.getStatus()))
                .collect(Collectors.toList());
            return ResponseEntity.ok(unack);
        } catch (Exception e) {
            log.error(
                "Error fetching unacknowledged anomalies: {}",
                e.getMessage()
            );
            return ResponseEntity.status(
                HttpStatus.INTERNAL_SERVER_ERROR
            ).build();
        }
    }

    // --- Action Endpoints ---

    @PostMapping("/{id}/acknowledge")
    public ResponseEntity<Boolean> acknowledgeAnomaly(
        @PathVariable Long id,
        @RequestParam(required = false) String username
    ) {
        try {
            boolean success = anomalyService.acknowledgeAnomaly(id);
            return ResponseEntity.ok(success);
        } catch (Exception e) {
            log.error("Error acknowledging anomaly {}: {}", id, e.getMessage());
            return ResponseEntity.status(
                HttpStatus.INTERNAL_SERVER_ERROR
            ).build();
        }
    }

    @PostMapping("/{id}/resolve")
    public ResponseEntity<Boolean> resolveAnomaly(@PathVariable Long id) {
        try {
            boolean success = anomalyService.resolveAnomaly(id);
            return ResponseEntity.ok(success);
        } catch (Exception e) {
            log.error("Error resolving anomaly {}: {}", id, e.getMessage());
            return ResponseEntity.status(
                HttpStatus.INTERNAL_SERVER_ERROR
            ).build();
        }
    }

    // --- List All Anomalies ---
    
    @GetMapping("")
    public ResponseEntity<List<AnomalyResponse>> getAllAnomalies(
        @RequestParam(defaultValue = "100") int limit
    ) {
        try {
            List<AnomalyResponse> anomalies = anomalyService.getRecentAnomalies(limit);
            return ResponseEntity.ok(anomalies);
        } catch (Exception e) {
            log.error("Error fetching all anomalies: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    // --- Stats ---

    @GetMapping("/stats")
    public ResponseEntity<StatisticsResponse> getAnomalyStatistics(
        @RequestParam(defaultValue = "all") String apiName
    ) {
        try {
            // If no API name provided, pick first one or handle aggregate in service
            // For now, let's assume specific API stats or empty
            StatisticsResponse stats = anomalyService.getStatistics(
                apiName.equals("all") ? "default_api" : apiName
            );
            return ResponseEntity.ok(stats);
        } catch (Exception e) {
            log.error("Error fetching anomaly statistics: {}", e.getMessage());
            return ResponseEntity.status(
                HttpStatus.INTERNAL_SERVER_ERROR
            ).build();
        }
    }
}
