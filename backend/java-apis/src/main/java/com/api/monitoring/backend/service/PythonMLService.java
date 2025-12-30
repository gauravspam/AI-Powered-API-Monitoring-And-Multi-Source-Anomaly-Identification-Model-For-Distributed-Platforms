package com.api.monitoring.backend.service;

import com.api.monitoring.backend.dto.AnomalyResponse;
import com.api.monitoring.backend.dto.LogEntryRequest;
import com.api.monitoring.backend.dto.ModelInfoResponse;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.client.RestClientException;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.Map;

@Service
public class PythonMLService {
    
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    
    @Value("${python.service.url:http://localhost:8000}")
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
            
            // Call Python API
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
            
            // Call Python API
            String url = pythonServiceUrl + "/api/detect-batch";
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);
            
            // Parse response
            if (response.getBody() != null && (Boolean) response.getBody().get("success")) {
                java.util.List<Map<String, Object>> results = (java.util.List<Map<String, Object>>) response.getBody().get("data");
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
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            return response.getBody() != null && "healthy".equals(response.getBody().get("status"));
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * Get model information from Python service
     */
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
     * Build request body for Python API
     */
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
        body.put("timestamp", logEntry.getTimestamp() != null ? logEntry.getTimestamp() : 
                   LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
        return body;
    }

    /**
     * Map Python API response to AnomalyResponse
     */
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
        if (value == null) return null;
        if (value instanceof Integer) return (Integer) value;
        if (value instanceof Number) return ((Number) value).intValue();
        return null;
    }

    private Double getDoubleValue(Map<String, Object> map, String key) {
        Object value = map.get(key);
        if (value == null) return null;
        if (value instanceof Double) return (Double) value;
        if (value instanceof Number) return ((Number) value).doubleValue();
        return null;
    }

    private String getStringValue(Map<String, Object> map, String key) {
        Object value = map.get(key);
        return value != null ? value.toString() : null;
    }
}

