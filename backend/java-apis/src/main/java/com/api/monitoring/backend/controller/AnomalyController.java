package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.dto.AnomalyResponse;
import com.api.monitoring.backend.dto.HealthResponse;
import com.api.monitoring.backend.dto.LogEntryRequest;
import com.api.monitoring.backend.dto.ModelInfoResponse;
import com.api.monitoring.backend.dto.StatisticsResponse;
import com.api.monitoring.backend.service.AnomalyService;
import com.api.monitoring.backend.service.PythonMLService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/anomaly")
public class AnomalyController {
    private static final Logger logger = LoggerFactory.getLogger(AnomalyController.class);

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
            logger.info("Received anomaly detection request for API: {}", logEntry.getApiName());
            AnomalyResponse response = anomalyService.detectAnomaly(logEntry);
            logger.info("Anomaly detection completed for API: {} with status: {}", logEntry.getApiName(), response.getStatus());
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("Error processing anomaly detection for API: {}", logEntry.getApiName(), e);
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
            logger.info("Received batch anomaly detection request for {} logs", logEntries.length);
            List<AnomalyResponse> responses = anomalyService.detectBatchAnomalies(logEntries);
            logger.info("Batch anomaly detection completed for {} logs", logEntries.length);
            return ResponseEntity.ok(responses);
        } catch (Exception e) {
            logger.error("Error processing batch anomaly detection", e);
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
            logger.info("Fetching recent anomalies for API: {}", apiName);
            List<AnomalyResponse> anomalies = anomalyService.getRecentAnomalies(apiName, 100);
            logger.info("Found {} recent anomalies for API: {}", anomalies.size(), apiName);
            return ResponseEntity.ok(anomalies);
        } catch (Exception e) {
            logger.error("Error fetching recent anomalies for API: {}", apiName, e);
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
            logger.info("Fetching all recent anomalies with limit: {}", limit);
            List<AnomalyResponse> anomalies = anomalyService.getAllRecentAnomalies(limit);
            logger.info("Found {} recent anomalies", anomalies.size());
            return ResponseEntity.ok(anomalies);
        } catch (Exception e) {
            logger.error("Error fetching all recent anomalies", e);
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
            logger.info("Fetching statistics for API: {}", apiName);
            StatisticsResponse stats = anomalyService.getStatistics(apiName);
            logger.info("Successfully fetched statistics for API: {}", apiName);
            return ResponseEntity.ok(stats);
        } catch (Exception e) {
            logger.error("Error fetching statistics for API: {}", apiName, e);
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
            logger.info("Performing health check");
            HealthResponse health = new HealthResponse();
            
            // Check Python service status
            boolean pythonStatus = pythonMLService.checkHealth();
            health.setPythonServiceStatus(pythonStatus);
            logger.info("Python service status: {}", pythonStatus);
            
            // Database status (assuming healthy for now)
            health.setDatabaseStatus(true);
            logger.info("Database status: healthy");
            
            // Get monitored APIs count
            int totalApis = anomalyService.getMonitoredApis().size();
            health.setTotalApisMonitored(totalApis);
            logger.info("Total APIs monitored: {}", totalApis);
            
            // Get active alerts count
            long activeAlerts = anomalyService.getActiveAlertsCount();
            health.setActiveAlerts((int) activeAlerts);
            logger.info("Active alerts count: {}", activeAlerts);
            
            // Processing latency (mock for now)
            health.setProcessingLatencyMs(67L);
            logger.info("Processing latency: 67ms");
            
            // Uptime percentage (mock for now)
            health.setUptimePercentage(99.98);
            logger.info("Uptime percentage: 99.98%");
            
            // Overall status
            if (pythonStatus) {
                health.setStatus("healthy");
            } else {
                health.setStatus("degraded");
            }
            logger.info("Overall system status: {}", health.getStatus());
            
            return ResponseEntity.ok(health);
        } catch (Exception e) {
            logger.error("Error during health check", e);
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
            logger.info("Fetching model information");
            ModelInfoResponse modelInfo = pythonMLService.getModelInfo();
            logger.info("Successfully fetched model information");
            return ResponseEntity.ok(modelInfo);
        } catch (Exception e) {
            logger.error("Error fetching model information", e);
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
            logger.info("Acknowledging anomaly with ID: {}", id);
            boolean acknowledged = anomalyService.acknowledgeAnomaly(id);
            if (acknowledged) {
                logger.info("Anomaly with ID: {} acknowledged successfully", id);
                return ResponseEntity.ok().build();
            } else {
                logger.warn("Anomaly with ID: {} not found", id);
                return ResponseEntity.notFound().build();
            }
        } catch (Exception e) {
            logger.error("Error acknowledging anomaly with ID: {}", id, e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}
