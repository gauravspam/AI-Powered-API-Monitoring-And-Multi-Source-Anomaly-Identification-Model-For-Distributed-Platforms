package com.api.monitoring.controller;

import com.api.monitoring.dto.AnomalyDTO;
import com.api.monitoring.dto.DashboardDTO;
import com.api.monitoring.entity.AnomalyScore;
import com.api.monitoring.service.AnomalyService;
import com.api.monitoring.service.LoggingService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Controller for Dashboard API endpoints
 */
@RestController
@RequestMapping("/api/v1/dashboard")
@CrossOrigin(origins = {"http://localhost:3000", "http://localhost:3001"})
@Slf4j
public class DashboardController {
    
    @Autowired
    private AnomalyService anomalyService;
    
    @Autowired
    private LoggingService loggingService;
    
    /**
     * Get recent anomalies with pagination
     */
    @GetMapping("/anomalies")
    public ResponseEntity<List<AnomalyDTO>> getRecentAnomalies(
            @RequestParam(defaultValue = "20") int limit) {
        
        try {
            List<AnomalyScore> anomalies = anomalyService.getLatestAnomalies(limit);
            
            List<AnomalyDTO> dtos = anomalies.stream()
                .map(this::convertToDTO)
                .collect(Collectors.toList());
            
            return ResponseEntity.ok(dtos);
            
        } catch (Exception e) {
            log.error("Error fetching anomalies", e);
            return ResponseEntity.status(500).build();
        }
    }
    
    /**
     * Get critical anomalies only
     */
    @GetMapping("/anomalies/critical")
    public ResponseEntity<List<AnomalyDTO>> getCriticalAnomalies(
            @RequestParam(defaultValue = "10") int limit) {
        
        try {
            List<AnomalyScore> anomalies = anomalyService.getCriticalAnomalies(limit);
            
            List<AnomalyDTO> dtos = anomalies.stream()
                .map(this::convertToDTO)
                .collect(Collectors.toList());
            
            return ResponseEntity.ok(dtos);
            
        } catch (Exception e) {
            log.error("Error fetching critical anomalies", e);
            return ResponseEntity.status(500).build();
        }
    }
    
    /**
     * Get complete dashboard summary
     */
    @GetMapping("/summary")
    public ResponseEntity<DashboardDTO> getDashboardSummary() {
        
        try {
            DashboardDTO summary = new DashboardDTO();
            
            Map<String, Object> stats = anomalyService.getAnomalyStats();
            
            @SuppressWarnings("unchecked")
            List<AnomalyScore> latestAnomalies = 
                (List<AnomalyScore>) stats.get("latest_anomalies");
            
            summary.setRecentAnomalies(
                latestAnomalies.stream()
                    .map(this::convertToDTO)
                    .collect(Collectors.toList())
            );
            
            summary.setTotalAnomaliesLast24h(
                ((Number) stats.get("total_last_24h")).intValue()
            );
            
            summary.setCriticalCount(
                ((Number) stats.get("critical_count")).intValue()
            );
            
            summary.setHighCount(
                ((Number) stats.get("high_count")).intValue()
            );
            
            summary.setAvgResponseTime(145.5);
            summary.setErrorCount(3);
            
            return ResponseEntity.ok(summary);
            
        } catch (Exception e) {
            log.error("Error fetching dashboard summary", e);
            return ResponseEntity.status(500).build();
        }
    }
    
    /**
     * Generate a test anomaly with random score
     */
    @PostMapping("/test-anomaly")
    public ResponseEntity<Map<String, Object>> generateTestAnomaly() {
        
        try {
            double fakeScore = 0.5 + (Math.random() * 0.5);
            
            AnomalyScore saved = anomalyService.saveAnomalyScore(
                "/api/v1/orders",
                "POST",
                "RESPONSE_TIME",
                fakeScore
            );
            
            loggingService.logAnomaly(
                "TEST_ANOMALY",
                fakeScore,
                "Test anomaly generated for pipeline testing"
            );
            
            Map<String, Object> response = new HashMap<>();
            response.put("id", saved.getId());
            response.put("score", fakeScore);
            response.put("severity", saved.getSeverity());
            response.put("status", "created");
            response.put("endpoint", saved.getApiEndpoint());
            response.put("timestamp", saved.getTimestamp());
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("Error generating test anomaly", e);
            return ResponseEntity.status(500)
                .body(Map.of("error", e.getMessage()));
        }
    }
    
    /**
     * Health check endpoint
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> healthCheck() {
        return ResponseEntity.ok(
            Map.of("status", "OK", "service", "api-monitoring-dashboard")
        );
    }
    
    /**
     * Convert AnomalyScore entity to DTO
     */
    private AnomalyDTO convertToDTO(AnomalyScore anomaly) {
        AnomalyDTO dto = new AnomalyDTO();
        dto.setId(anomaly.getId());
        dto.setApiEndpoint(anomaly.getApiEndpoint());
        dto.setAnomalyType(anomaly.getAnomalyType());
        dto.setScore(anomaly.getScore());
        dto.setSeverity(anomaly.getSeverity());
        dto.setTimestamp(anomaly.getTimestamp());
        return dto;
    }
}