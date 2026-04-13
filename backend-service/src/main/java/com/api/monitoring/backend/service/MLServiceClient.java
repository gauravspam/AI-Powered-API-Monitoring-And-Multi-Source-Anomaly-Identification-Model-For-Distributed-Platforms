package com.api.monitoring.backend.service;

import com.api.monitoring.backend.dto.AnomalyPredictionDTO;
import com.api.monitoring.backend.dto.MLPredictionResponse;
import com.api.monitoring.backend.model.LogRecord;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.http.*;
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.Retryable;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@Slf4j
public class MLServiceClient {

    private final RestTemplate restTemplate;

    @Value("${python.service.url:http://localhost:9000}")
    private String mlServiceUrl;

    @Value("${python.service.enabled:true}")
    private boolean mlServiceEnabled;

    @Value("${python.service.timeout:30}")
    private int timeoutSeconds;

    @Value("${python.service.version:1.0.0}")
    private String mlServiceVersion;

    @Autowired
    public MLServiceClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    @Retryable(
        value = {ResourceAccessException.class, HttpServerErrorException.class},
        maxAttempts = 3,
        backoff = @Backoff(delay = 1000, multiplier = 2, maxDelay = 10000)
    )
    public AnomalyPredictionDTO predictAnomaly(LogRecord logRecord) {
        long startTime = System.currentTimeMillis();
        
        if (!mlServiceEnabled) {
            log.warn("ML Service is disabled. Returning default prediction.");
            return createDefaultPrediction(logRecord);
        }

        try {
            log.info("Calling ML Service for log ID: {}, endpoint: {}", 
                    logRecord.getId(), logRecord.getEndpoint());

            Map<String, Object> requestPayload = buildPredictionRequest(logRecord);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("X-Trace-Id", logRecord.getTraceId() != null ? logRecord.getTraceId() : "unknown");
            headers.set("X-Request-Source", "backend-service");

            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestPayload, headers);

            String endpoint = mlServiceUrl + "/predict";
            log.debug("POST {}", endpoint);
            log.debug("Request body: {}", requestPayload);

            ResponseEntity<MLPredictionResponse> response = restTemplate.exchange(
                endpoint,
                HttpMethod.POST,
                request,
                MLPredictionResponse.class
            );

            long duration = System.currentTimeMillis() - startTime;

            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                MLPredictionResponse mlResponse = response.getBody();
                
                log.info("✅ ML prediction SUCCESS for log {}: hybrid_score={}, severity={}, duration={}ms",
                        logRecord.getId(), 
                        mlResponse.getHybridScore(),
                        mlResponse.getSeverity(),
                        duration);

                return convertToAnomalyPredictionDTO(mlResponse, logRecord, duration);
            } else {
                log.error("ML Service returned non-OK status: {}", response.getStatusCode());
                throw new MLServiceException("ML Service returned status: " + response.getStatusCode());
            }

        } catch (HttpClientErrorException e) {
            log.error("❌ ML Service client error (4xx) for log {}: {} - {}",
                    logRecord.getId(), e.getStatusCode(), e.getResponseBodyAsString());
            throw new MLServiceException("Client error calling ML service: " + e.getMessage(), e);

        } catch (HttpServerErrorException e) {
            log.error("❌ ML Service server error (5xx) for log {}: {} - Will retry",
                    logRecord.getId(), e.getStatusCode());
            throw e;

        } catch (ResourceAccessException e) {
            log.error("❌ ML Service network error for log {}: {} - Will retry",
                    logRecord.getId(), e.getMessage());
            throw e;

        } catch (Exception e) {
            log.error("❌ Unexpected error calling ML Service for log {}: {}",
                    logRecord.getId(), e.getMessage(), e);
            throw new MLServiceException("Unexpected error: " + e.getMessage(), e);
        }
    }

    @SuppressWarnings("unchecked")
    public AnomalyPredictionDTO predictAnomalyMultimodal(
            LogRecord logRecord,
            List<Map<String, String>> logs,
            List<Map<String, Object>> traces,
            Map<String, Object> metrics) {
        long startTime = System.currentTimeMillis();
        
        if (!mlServiceEnabled) {
            log.warn("ML Service is disabled. Returning default prediction.");
            return createDefaultPrediction(logRecord);
        }

        try {
            log.info("Calling ML Service (multimodal) for endpoint: {}", logRecord.getEndpoint());

            Map<String, Object> requestPayload = new HashMap<>();
            
            // Add metrics if provided
            if (metrics != null) {
                requestPayload.put("metrics", metrics);
            } else {
                // Fallback to log record fields
                Map<String, Object> fallbackMetrics = new HashMap<>();
                fallbackMetrics.put("cpu_usage", logRecord.getCpuUsage() != null ? logRecord.getCpuUsage() : 0.0);
                fallbackMetrics.put("memory_usage", logRecord.getMemoryUsage() != null ? logRecord.getMemoryUsage() : 0.0);
                fallbackMetrics.put("response_time_ms", logRecord.getResponseTimeMs() != null ? logRecord.getResponseTimeMs() : 0);
                fallbackMetrics.put("error_rate", logRecord.getErrorRate() != null ? logRecord.getErrorRate() : 0.0);
                requestPayload.put("metrics", fallbackMetrics);
            }
            
            // Add logs if provided
            if (logs != null && !logs.isEmpty()) {
                requestPayload.put("logs", logs);
            }
            
            // Add traces if provided
            if (traces != null && !traces.isEmpty()) {
                requestPayload.put("traces", traces);
            }

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("X-Trace-Id", logRecord.getTraceId() != null ? logRecord.getTraceId() : "unknown");
            headers.set("X-Request-Source", "backend-service-multimodal");

            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestPayload, headers);

            String endpoint = mlServiceUrl + "/predict/flexible";
            log.debug("POST {} (multimodal)", endpoint);
            log.debug("Request body: {}", requestPayload);

            ResponseEntity<Map> response = restTemplate.exchange(
                endpoint,
                HttpMethod.POST,
                request,
                Map.class
            );

            long duration = System.currentTimeMillis() - startTime;

            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                Map<String, Object> mlResponse = response.getBody();
                
                Double finalScore = ((Number) mlResponse.getOrDefault("final_score", 0.0)).doubleValue();
                String severity = (String) mlResponse.getOrDefault("severity", "NORMAL");
                Double confidence = ((Number) mlResponse.getOrDefault("confidence", 0.5)).doubleValue();
                Double msifScore = ((Number) mlResponse.getOrDefault("msif_score", 0.0)).doubleValue();
                Double pleScore = ((Number) mlResponse.getOrDefault("ple_score", 0.0)).doubleValue();
                String fusionMethod = (String) mlResponse.getOrDefault("fusion_method", "flexible_multimodal");
                
                log.info("✅ ML prediction SUCCESS (multimodal): final_score={}, severity={}, duration={}ms",
                        finalScore, severity, duration);

                return AnomalyPredictionDTO.builder()
                        .logId(logRecord.getId())
                        .endpoint(logRecord.getEndpoint())
                        .method(logRecord.getMethod())
                        .msifScore(msifScore)
                        .pleScore(pleScore)
                        .hybridScore(finalScore)
                        .severity(severity)
                        .confidence(confidence)
                        .fusionMethod(fusionMethod)
                        .mlProcessingTimeMs(duration)
                        .mlServiceVersion(mlServiceVersion)
                        .traceId(logRecord.getTraceId())
                        .timestamp(LocalDateTime.now())
                        .build();
            } else {
                log.error("ML Service (multimodal) returned non-OK status: {}", response.getStatusCode());
                throw new MLServiceException("ML Service returned status: " + response.getStatusCode());
            }

        } catch (HttpClientErrorException e) {
            log.error("❌ ML Service (multimodal) client error: {} - {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new MLServiceException("Client error calling ML service: " + e.getMessage(), e);

        } catch (HttpServerErrorException e) {
            log.error("❌ ML Service (multimodal) server error: {}", e.getStatusCode());
            throw e;

        } catch (ResourceAccessException e) {
            log.error("❌ ML Service (multimodal) network error: {}", e.getMessage());
            throw e;

        } catch (Exception e) {
            log.error("❌ Unexpected error calling ML Service (multimodal): {}", e.getMessage(), e);
            throw new MLServiceException("Unexpected error: " + e.getMessage(), e);
        }
    }

    private Map<String, Object> buildPredictionRequest(LogRecord logRecord) {
        Map<String, Object> payload = new HashMap<>();

        payload.put("endpoint", logRecord.getEndpoint());
        payload.put("method", logRecord.getMethod());
        payload.put("response_time", logRecord.getResponseTimeMs() != null ? logRecord.getResponseTimeMs() : 0);
        payload.put("status_code", logRecord.getStatusCode() != null ? logRecord.getStatusCode() : 200);
        payload.put("cpu_usage", logRecord.getCpuUsage() != null ? logRecord.getCpuUsage() : 0.0);
        payload.put("memory_usage", logRecord.getMemoryUsage() != null ? logRecord.getMemoryUsage() : 0.0);
        payload.put("error_rate", logRecord.getErrorRate() != null ? logRecord.getErrorRate() : 0.0);
        payload.put("network_io", logRecord.getNetworkIo() != null ? logRecord.getNetworkIo() : 0);
        payload.put("disk_io", logRecord.getDiskIo() != null ? logRecord.getDiskIo() : 0);
        payload.put("request_count", logRecord.getRequestCount() != null ? logRecord.getRequestCount() : 1);
        payload.put("hour_of_day", logRecord.getHourOfDay() != null ? logRecord.getHourOfDay() : 
                    LocalDateTime.now().getHour());
        payload.put("day_of_week", logRecord.getDayOfWeek() != null ? logRecord.getDayOfWeek() : 
                    LocalDateTime.now().getDayOfWeek().getValue());
        
        Map<String, Object> context = new HashMap<>();
        context.put("trace_id", logRecord.getTraceId());
        context.put("environment", logRecord.getEnvironment() != null ? logRecord.getEnvironment() : "production");
        context.put("service_name", logRecord.getServiceName() != null ? logRecord.getServiceName() : "unknown");
        payload.put("context", context);

        return payload;
    }

    private AnomalyPredictionDTO convertToAnomalyPredictionDTO(
            MLPredictionResponse mlResponse, 
            LogRecord logRecord, 
            long processingTimeMs) {
        
        return AnomalyPredictionDTO.builder()
                .logId(logRecord.getId())
                .endpoint(logRecord.getEndpoint())
                .method(logRecord.getMethod())
                .msifScore(mlResponse.getMsifScore())
                .pleScore(mlResponse.getPleScore())
                .hybridScore(mlResponse.getHybridScore())
                .severity(mlResponse.getSeverity())
                .confidence(mlResponse.getConfidenceValue())
                .fusionMethod(mlResponse.getFusionMethod() != null ? 
                             mlResponse.getFusionMethod() : "weighted_ensemble")
                .mlProcessingTimeMs(processingTimeMs)
                .mlServiceVersion(mlServiceVersion)
                .traceId(logRecord.getTraceId())
                .timestamp(LocalDateTime.now())
                .build();
    }

    private AnomalyPredictionDTO createDefaultPrediction(LogRecord logRecord) {
        return AnomalyPredictionDTO.builder()
                .logId(logRecord.getId())
                .endpoint(logRecord.getEndpoint())
                .method(logRecord.getMethod())
                .msifScore(0.0)
                .pleScore(0.0)
                .hybridScore(0.0)
                .severity("UNKNOWN")
                .confidence(0.0)
                .fusionMethod("none")
                .mlProcessingTimeMs(0L)
                .mlServiceVersion("disabled")
                .traceId(logRecord.getTraceId())
                .timestamp(LocalDateTime.now())
                .build();
    }

    @Cacheable(value = "mlServiceHealth", unless = "#result == false")
    public boolean isHealthy() {
        if (!mlServiceEnabled) {
            return false;
        }

        try {
            String healthEndpoint = mlServiceUrl + "/health";
            ResponseEntity<Map> response = restTemplate.getForEntity(healthEndpoint, Map.class);
            
            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                Map<String, Object> body = response.getBody();
                String status = (String) body.get("status");
                Boolean modelsLoaded = (Boolean) body.getOrDefault("models_loaded", false);
                
                log.debug("ML Service health: status={}, models_loaded={}", status, modelsLoaded);
                
                boolean healthy = "healthy".equalsIgnoreCase(status) || "UP".equalsIgnoreCase(status);
                boolean ready = modelsLoaded != null && modelsLoaded;
                
                return healthy && ready;
            }
            
            return false;

        } catch (Exception e) {
            log.warn("ML Service health check failed: {}", e.getMessage());
            return false;
        }
    }

    public Map<String, Object> getModelInfo() {
        try {
            String infoEndpoint = mlServiceUrl + "/api/model-info";
            ResponseEntity<Map> response = restTemplate.getForEntity(infoEndpoint, Map.class);
            
            if (response.getStatusCode() == HttpStatus.OK) {
                return response.getBody();
            }
            
            return null;

        } catch (Exception e) {
            log.warn("Failed to get ML service model info: {}", e.getMessage());
            return null;
        }
    }

    public static class MLServiceException extends RuntimeException {
        public MLServiceException(String message) {
            super(message);
        }

        public MLServiceException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
