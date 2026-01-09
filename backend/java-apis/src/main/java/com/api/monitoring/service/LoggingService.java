package com.api.monitoring.service;

import org.fluentd.logger.FluentLogger;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

/**
 * Service to handle logging of API calls and anomalies to Fluentd
 * Logs are sent to OpenSearch via Fluentd for real-time analysis
 */
@Service
public class LoggingService {
    
    private static final FluentLogger logger = 
        FluentLogger.getLogger("api-logs");

    
    private static final Logger LOGGER = 
        LoggerFactory.getLogger(LoggingService.class);
    
    /**
     * Log API call details to Fluentd
     */
    public void logApiCall(String endpoint, String method, 
                          int statusCode, long responseTimeMs) {
        logApiCall(endpoint, method, statusCode, responseTimeMs, null);
    }
    
    /**
     * Log API call with optional additional metadata
     */
    public void logApiCall(String endpoint, String method, 
                          int statusCode, long responseTimeMs,
                          Map<String, Object> additionalData) {
        try {
            Map<String, Object> logData = new HashMap<>();
            logData.put("timestamp", Instant.now().toString());
            logData.put("service", "api-monitoring-backend");
            logData.put("endpoint", endpoint);
            logData.put("method", method);
            logData.put("status", statusCode);
            logData.put("response_time_ms", responseTimeMs);
            logData.put("environment", "docker");
            
            // Add any additional metadata
            if (additionalData != null) {
                logData.putAll(additionalData);
            }
            
            // Send to Fluentd with tag "api-logs.backend"
            boolean success = logger.log("backend", logData);
            
            if (!success) {
                LOGGER.warn("Failed to queue log to Fluentd for endpoint: {}", endpoint);
            }
            
        } catch (Exception e) {
            LOGGER.error("Exception occurred while logging API call to {}", endpoint, e);
        }
    }
    
    /**
     * Log API errors
     */
    public void logApiError(String endpoint, String method, 
                           int statusCode, String errorMessage,
                           long responseTimeMs) {
        try {
            Map<String, Object> logData = new HashMap<>();
            logData.put("timestamp", Instant.now().toString());
            logData.put("service", "api-monitoring-backend");
            logData.put("endpoint", endpoint);
            logData.put("method", method);
            logData.put("status", statusCode);
            logData.put("error_message", errorMessage);
            logData.put("response_time_ms", responseTimeMs);
            logData.put("log_level", "ERROR");
            logData.put("environment", "docker");
            
            logger.log("backend", logData);
            
        } catch (Exception e) {
            LOGGER.error("Failed to log API error for {}", endpoint, e);
        }
    }
    
    /**
     * Log anomaly detection results
     */
    public void logAnomaly(String anomalyType, double score, 
                          String details) {
        logAnomaly(anomalyType, score, details, null);
    }
    
    /**
     * Log anomaly with additional metadata
     */
    public void logAnomaly(String anomalyType, double score, 
                          String details, Map<String, Object> additionalData) {
        try {
            Map<String, Object> logData = new HashMap<>();
            logData.put("timestamp", Instant.now().toString());
            logData.put("service", "api-monitoring-backend");
            logData.put("anomaly_type", anomalyType);
            logData.put("anomaly_score", score);
            logData.put("details", details);
            
            // Determine severity based on score
            String severity = determineSeverity(score);
            logData.put("severity", severity);
            logData.put("log_level", severity);
            logData.put("environment", "docker");
            
            // Add additional metadata if provided
            if (additionalData != null) {
                logData.putAll(additionalData);
            }
            
            // Send to Fluentd with tag "api-logs.anomalies"
            boolean success = logger.log("anomalies", logData);
            
            if (!success) {
                LOGGER.warn("Failed to queue anomaly log for type: {}", anomalyType);
            }
            
        } catch (Exception e) {
            LOGGER.error("Failed to log anomaly of type {}", anomalyType, e);
        }
    }
    
    /**
     * Log performance metrics
     */
    public void logMetrics(String endpoint, long responseTime,
                          int errorCount, int successCount) {
        try {
            Map<String, Object> logData = new HashMap<>();
            logData.put("timestamp", Instant.now().toString());
            logData.put("service", "api-monitoring-backend");
            logData.put("endpoint", endpoint);
            logData.put("response_time_ms", responseTime);
            logData.put("error_count", errorCount);
            logData.put("success_count", successCount);
            logData.put("total_requests", errorCount + successCount);
            logData.put("error_rate", 
                (double) errorCount / (errorCount + successCount));
            logData.put("log_type", "metrics");
            logData.put("environment", "docker");
            
            logger.log("metrics", logData);
            
        } catch (Exception e) {
            LOGGER.error("Failed to log metrics for {}", endpoint, e);
        }
    }
    
    /**
     * Determine severity level based on anomaly score
     */
    private String determineSeverity(double score) {
        if (score > 0.8) {
            return "CRITICAL";
        } else if (score > 0.6) {
            return "HIGH";
        } else if (score > 0.4) {
            return "MEDIUM";
        } else {
            return "LOW";
        }
    }
    
    /**
     * Flush any pending logs to Fluentd
     */
    public void flush() {
        try {
            logger.flush();
            LOGGER.info("Fluentd logger flushed successfully");
        } catch (Exception e) {
            LOGGER.error("Failed to flush Fluentd logger", e);
        }
    }
    
    /**
     * Close the Fluentd connection
     */
    public void close() {
        try {
            logger.close();
            LOGGER.info("Fluentd logger closed successfully");
        } catch (Exception e) {
            LOGGER.error("Failed to close Fluentd logger", e);
        }
    }
}