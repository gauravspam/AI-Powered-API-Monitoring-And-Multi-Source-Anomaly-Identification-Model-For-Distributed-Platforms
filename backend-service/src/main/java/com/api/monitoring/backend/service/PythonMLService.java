package com.api.monitoring.backend.service;

import com.api.monitoring.backend.dto.AnomalyResponse;
import com.api.monitoring.backend.dto.LogEntryRequest;
import com.api.monitoring.backend.dto.ModelInfoResponse;
import com.api.monitoring.backend.dto.AnomalyScoresResponse;
import com.api.monitoring.backend.dto.FeatureWindow;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.client.RestClientException;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.Map;

@SuppressWarnings({ "rawtypes", "unchecked" }) // ✅ This fixes the warning
@Service
public class PythonMLService {

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    @Value("${python.service.url:http://localhost:9000}")
    private String pythonServiceUrl;

    public PythonMLService(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
        this.objectMapper = new ObjectMapper();
    }

    /**
     * Call Python ML service to detect anomaly for a single log entry
     */
    public AnomalyResponse detectAnomaly(LogEntryRequest logEntry) {
        try {
            // Prepare request body
            Map<String, Object> requestBody = buildRequestBody(logEntry);

            // Set headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

            // Call Python API - YOUR ORIGINAL CODE (WORKS PERFECTLY)
            String url = pythonServiceUrl + "/api/detect-anomaly";
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);

            // Parse response
            if (response.getBody() != null && (Boolean) response.getBody().get("success")) {
                Map<String, Object> data = (Map<String, Object>) response.getBody().get("data");
                return mapToAnomalyResponse(data, logEntry.getApiName());
            }

            throw new RuntimeException("Python service returned unsuccessful response");
        } catch (RestClientException e) {
            throw new RuntimeException("Failed to call Python ML service: " + e.getMessage(), e);
        }
    }

    /**
     * Call Python ML service to detect anomalies for batch of log entries
     */
    public AnomalyResponse[] detectBatchAnomalies(LogEntryRequest[] logEntries) {
        try {
            // Prepare request body
            Map<String, Object> requestBody = new HashMap<>();
            java.util.List<Map<String, Object>> logs = new java.util.ArrayList<>();
            for (LogEntryRequest entry : logEntries) {
                logs.add(buildRequestBody(entry));
            }
            requestBody.put("logs", logs);

            // Set headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

            // Call Python API - YOUR ORIGINAL CODE (WORKS PERFECTLY)
            String url = pythonServiceUrl + "/api/detect-batch";
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);

            // Parse response
            if (response.getBody() != null && (Boolean) response.getBody().get("success")) {
                java.util.List<Map<String, Object>> results = (java.util.List<Map<String, Object>>) response.getBody()
                        .get("data");
                AnomalyResponse[] responses = new AnomalyResponse[results.size()];
                for (int i = 0; i < results.size() && i < logEntries.length; i++) {
                    Map<String, Object> data = results.get(i);
                    // Use api_name from response if available, otherwise from original request
                    String apiName = (String) data.get("api_name");
                    if (apiName == null || apiName.isEmpty()) {
                        apiName = logEntries[i].getApiName();
                    }
                    responses[i] = mapToAnomalyResponse(data, apiName);
                }
                return responses;
            }

            throw new RuntimeException("Python service returned unsuccessful response");
        } catch (RestClientException e) {
            throw new RuntimeException("Failed to call Python ML service: " + e.getMessage(), e);
        }
    }

    /**
     * Check Python service health
     */
    public boolean checkHealth() {
        try {
            String url = pythonServiceUrl + "/health";
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class); // ✅ Original works
            return response.getBody() != null && "healthy".equals(response.getBody().get("status"));
        } catch (Exception e) {
            return false;
        }
    }

    public ModelInfoResponse getModelInfo() {
        try {
            String url = pythonServiceUrl + "/api/model-info";
            ResponseEntity<ModelInfoResponse> response = restTemplate.getForEntity(url, ModelInfoResponse.class);
            return response.getBody();
        } catch (Exception e) {
            // Return default model info if service is unavailable
            ModelInfoResponse defaultInfo = new ModelInfoResponse();
            defaultInfo.setStage1Model("MSIF-LSTM");
            defaultInfo.setStage2Model("PLE-GRU");
            defaultInfo.setConfidenceThresholdStage1(0.3);
            defaultInfo.setConfidenceThresholdStage2(0.7);
            defaultInfo.setFeatures(10);
            defaultInfo.setDescription("Two-stage anomaly detection system");
            return defaultInfo;
        }
    }

    /**
     * NEW: Call Python ML service with time-series feature windows
     * This is for scheduled anomaly detection jobs (Phase 2)
     * Existing detectAnomaly() and detectBatchAnomalies() remain unchanged
     */
    private static final Logger logger = LoggerFactory.getLogger(PythonMLService.class);

    public AnomalyScoresResponse predictWithFeatures(
            FeatureWindow featureWindow,
            String traceId) {
        long startTime = System.currentTimeMillis();

        try {
            logger.info("[{}] Calling ML service /predict for endpoint: {} method: {}",
                    traceId, featureWindow.getEndpoint(), featureWindow.getMethod());

            // Build request
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("X-Trace-ID", traceId);
            HttpEntity<FeatureWindow> request = new HttpEntity<>(featureWindow, headers);

            // Call NEW endpoint: /api/predict (different from /api/detect-anomaly)
            String url = pythonServiceUrl + "/api/predict";

            // Retry logic: 3 attempts with 2s delay
            ResponseEntity<Map> response = null;
            int maxRetries = 3;
            int retryDelay = 2000; // 2 seconds

            for (int attempt = 1; attempt <= maxRetries; attempt++) {
                try {
                    response = restTemplate.postForEntity(url, request, Map.class);
                    break; // Success, exit retry loop
                } catch (RestClientException e) {
                    logger.warn("[{}] Attempt {}/{} failed: {}", traceId, attempt, maxRetries, e.getMessage());
                    if (attempt < maxRetries) {
                        Thread.sleep(retryDelay);
                        retryDelay *= 2; // Exponential backoff: 2s, 4s, 8s
                    } else {
                        throw e; // Final attempt failed
                    }
                }
            }

            // Parse response
            if (response != null && response.getBody() != null) {
                Map<String, Object> body = response.getBody();

                AnomalyScoresResponse scores = new AnomalyScoresResponse();
                scores.setMsifLstmScore(getDoubleValue(body, "msif_lstm_score"));
                scores.setPleGruScore(getDoubleValue(body, "ple_gru_score"));
                scores.setHybridScore(getDoubleValue(body, "hybrid_score"));
                scores.setConfidence(getDoubleValue(body, "confidence"));
                scores.setFusionMethod(getStringValue(body, "fusion_method"));
                scores.setContext(getStringValue(body, "context"));

                // Set processing time
                long processingTime = System.currentTimeMillis() - startTime;
                scores.setProcessingTimeMs(processingTime);

                logger.info("[{}] ML predictions received in {}ms: MSIF={} PLE={} Hybrid={}",
                        traceId, processingTime,
                        String.format("%.2f", scores.getMsifLstmScore()),
                        String.format("%.2f", scores.getPleGruScore()),
                        String.format("%.2f", scores.getHybridScore()));

                return scores;
            }

            throw new RuntimeException("Python service returned null response");

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            logger.error("[{}] Retry interrupted: {}", traceId, e.getMessage());
            return getFallbackScores(featureWindow, traceId);
        } catch (Exception e) {
            logger.error("[{}] ML service failed: {}", traceId, e.getMessage(), e);
            return getFallbackScores(featureWindow, traceId);
        }
    }

    /**
     * NEW: Fallback when ML service is unavailable
     * Returns conservative default scores
     */
    private AnomalyScoresResponse getFallbackScores(FeatureWindow featureWindow, String traceId) {
        logger.warn("[{}] Using fallback scores (ML service unavailable)", traceId);

        AnomalyScoresResponse fallback = new AnomalyScoresResponse();
        fallback.setMsifLstmScore(0.0);
        fallback.setPleGruScore(0.0);
        fallback.setHybridScore(0.0);
        fallback.setConfidence(0.0);
        fallback.setFusionMethod("fallback_default");
        fallback.setContext("ML service unavailable");

        return fallback;
    }

    private Map<String, Object> buildRequestBody(LogEntryRequest logEntry) {
        Map<String, Object> body = new HashMap<>();
        body.put("api_name", logEntry.getApiName());
        body.put("response_time", logEntry.getResponseTime());
        body.put("status_code", logEntry.getStatusCode());
        body.put("request_count", logEntry.getRequestCount());
        body.put("error_rate", logEntry.getErrorRate());
        body.put("cpu_usage", logEntry.getCpuUsage());
        body.put("memory_usage", logEntry.getMemoryUsage());
        body.put("network_io", logEntry.getNetworkIo());
        body.put("disk_io", logEntry.getDiskIo());
        body.put("hour_of_day", logEntry.getHourOfDay());
        body.put("day_of_week", logEntry.getDayOfWeek());
        body.put("timestamp", logEntry.getTimestamp() != null ? logEntry.getTimestamp()
                : LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
        return body;
    }

    private AnomalyResponse mapToAnomalyResponse(Map<String, Object> data, String apiName) {
        AnomalyResponse response = new AnomalyResponse();
        response.setApiName(apiName);
        response.setStage(getIntegerValue(data, "stage"));
        response.setModel(getStringValue(data, "model"));
        response.setAnomalyScore(getDoubleValue(data, "anomaly_score"));
        response.setStage2Score(getDoubleValue(data, "stage2_score"));
        response.setFinalAnomalyScore(getDoubleValue(data, "final_anomaly_score"));
        response.setStatus(getStringValue(data, "status"));
        response.setSeverity(getStringValue(data, "severity"));
        response.setConfidence(getDoubleValue(data, "confidence"));

        // Set timestamp
        if (data.containsKey("timestamp")) {
            response.setTimestamp(data.get("timestamp").toString());
        } else {
            response.setTimestamp(LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
        }

        return response;
    }

    private Integer getIntegerValue(Map<String, Object> map, String key) {
        Object value = map.get(key);
        if (value == null)
            return null;
        if (value instanceof Integer)
            return (Integer) value;
        if (value instanceof Number)
            return ((Number) value).intValue();
        return null;
    }

    private Double getDoubleValue(Map<String, Object> map, String key) {
        Object value = map.get(key);
        if (value == null)
            return null;
        if (value instanceof Double)
            return (Double) value;
        if (value instanceof Number)
            return ((Number) value).doubleValue();
        return null;
    }

    private String getStringValue(Map<String, Object> map, String key) {
        Object value = map.get(key);
        return value != null ? value.toString() : null;
    }
}
