package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.dto.AnomalyResponse;
import com.api.monitoring.backend.dto.HealthResponse;
import com.api.monitoring.backend.dto.LogEntryRequest;
import com.api.monitoring.backend.dto.ModelInfoResponse;
import com.api.monitoring.backend.dto.StatisticsResponse;
import com.api.monitoring.backend.service.AnomalyService;
import com.api.monitoring.backend.service.PythonMLService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/anomalies")
public class AnomalyController {

    private final AnomalyService anomalyService;
    private final PythonMLService pythonMLService;

    public AnomalyController(AnomalyService anomalyService, PythonMLService pythonMLService) {
        this.anomalyService = anomalyService;
        this.pythonMLService = pythonMLService;
    }

    /**
     * 1. Single Anomaly Detection
     * POST /api/v1/anomalies/detect
     */
    @PostMapping("/detect")
    public ResponseEntity<AnomalyResponse> detectAnomaly(@RequestBody LogEntryRequest logEntry) {
        try {
            AnomalyResponse response = anomalyService.detectAnomaly(logEntry);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * 2. Batch Anomaly Detection
     * POST /api/v1/anomalies/detect-batch
     */
    @PostMapping("/detect-batch")
    public ResponseEntity<List<AnomalyResponse>> detectBatchAnomalies(@RequestBody LogEntryRequest[] logEntries) {
        try {
            List<AnomalyResponse> responses = anomalyService.detectBatchAnomalies(logEntries);
            return ResponseEntity.ok(responses);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * 3. Get Recent Anomalies for specific API
     * GET /api/v1/anomalies/recent/{api_name}
     */
    @GetMapping("/recent/{api_name}")
    public ResponseEntity<List<AnomalyResponse>> getRecentAnomalies(
            @PathVariable("api_name") String apiName) {
        try {
            List<AnomalyResponse> anomalies = anomalyService.getRecentAnomalies(apiName, 100);
            return ResponseEntity.ok(anomalies);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * 6. Get All Recent Anomalies
     * GET /api/v1/anomalies/recent-all?limit=50
     */
    @GetMapping("/recent-all")
    public ResponseEntity<List<AnomalyResponse>> getAllRecentAnomalies(
            @RequestParam(value = "limit", defaultValue = "50") int limit) {
        try {
            List<AnomalyResponse> anomalies = anomalyService.getAllRecentAnomalies(limit);
            return ResponseEntity.ok(anomalies);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * 4. Get API Statistics
     * GET /api/v1/anomalies/statistics/{api_name}
     */
    @GetMapping("/statistics/{api_name}")
    public ResponseEntity<StatisticsResponse> getStatistics(
            @PathVariable("api_name") String apiName) {
        try {
            StatisticsResponse stats = anomalyService.getStatistics(apiName);
            return ResponseEntity.ok(stats);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * 5. Health Check
     * GET /api/v1/anomalies/health
     */
    @GetMapping("/health")
    public ResponseEntity<HealthResponse> getHealth() {
        try {
            HealthResponse health = new HealthResponse();
            
            // Check Python service status
            boolean pythonStatus = pythonMLService.checkHealth();
            health.setPythonServiceStatus(pythonStatus);
            
            // Database status (assuming healthy for now)
            health.setDatabaseStatus(true);
            
            // Get monitored APIs count
            int totalApis = anomalyService.getMonitoredApis().size();
            health.setTotalApisMonitored(totalApis);
            
            // Get active alerts count
            long activeAlerts = anomalyService.getActiveAlertsCount();
            health.setActiveAlerts((int) activeAlerts);
            
            // Processing latency (mock for now)
            health.setProcessingLatencyMs(67L);
            
            // Uptime percentage (mock for now)
            health.setUptimePercentage(99.98);
            
            // Overall status
            if (pythonStatus) {
                health.setStatus("healthy");
            } else {
                health.setStatus("degraded");
            }
            
            return ResponseEntity.ok(health);
        } catch (Exception e) {
            HealthResponse health = new HealthResponse();
            health.setStatus("unhealthy");
            health.setPythonServiceStatus(false);
            health.setDatabaseStatus(false);
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(health);
        }
    }

    /**
     * 7. Get Model Information
     * GET /api/v1/anomalies/model-info
     */
    @GetMapping("/model-info")
    public ResponseEntity<ModelInfoResponse> getModelInfo() {
        try {
            ModelInfoResponse modelInfo = pythonMLService.getModelInfo();
            return ResponseEntity.ok(modelInfo);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * 8. Acknowledge Anomaly
     * DELETE /api/v1/anomalies/{id}/acknowledge
     */
    @DeleteMapping("/{id}/acknowledge")
    public ResponseEntity<Void> acknowledgeAnomaly(@PathVariable Long id) {
        try {
            boolean acknowledged = anomalyService.acknowledgeAnomaly(id);
            if (acknowledged) {
                return ResponseEntity.ok().build();
            } else {
                return ResponseEntity.notFound().build();
            }
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}
