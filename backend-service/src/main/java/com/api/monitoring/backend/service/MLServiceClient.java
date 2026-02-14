package com.api.monitoring.backend.service;

import com.api.monitoring.backend.dto.ml.PredictionResponseDto;
import com.api.monitoring.backend.dto.ml.PredictionWindowDto;
import com.api.monitoring.backend.model.LogRecord;
import com.api.monitoring.backend.model.MetricRecord;
import com.api.monitoring.backend.model.TraceRecord;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class MLServiceClient {

    private final RestTemplate restTemplate;
    private final MultimodalDataAggregator aggregator;

    @Value("${ml.service.url:http://localhost:9000}")
    private String mlServiceUrl;

    public PredictionResponseDto detectAnomaly(
            List<MetricRecord> ignoredMetrics,
            List<LogRecord> ignoredLogs,
            List<TraceRecord> ignoredTraces,
            String serviceName,
            Instant windowStart,
            Instant windowEnd) {
        try {
            PredictionWindowDto window = aggregator.aggregateWindow(serviceName, windowStart, windowEnd);
            return callMlService(window);
        } catch (Exception e) {
            log.error("❌ ML service call failed: {}", e.getMessage());
            return createFallbackResponse(serviceName);
        }
    }

    public PredictionResponseDto detectAnomalyDirect(PredictionWindowDto window) {
        try {
            return callMlService(window);
        } catch (Exception e) {
            log.error("❌ ML service call failed (Direct): {}", e.getMessage());
            String serviceName = (window.getContext() != null) ? window.getContext().get("service_name") : "unknown";
            return createFallbackResponse(serviceName);
        }
    }

    private PredictionResponseDto callMlService(PredictionWindowDto window) {
        try {
            PredictionResponseDto response = restTemplate.postForObject(
                    mlServiceUrl + "/v1/predict",
                    window,
                    PredictionResponseDto.class);

            if (response == null) {
                throw new RuntimeException("Received null response from ML Service");
            }

            if (response.getResult() == null) {
                PredictionResponseDto.AnomalyScoreResult result = new PredictionResponseDto.AnomalyScoreResult();

                if (response.getFlatIsAnomaly() != null) {
                    result.setAnomaly(response.getFlatIsAnomaly());
                }

                if (response.getFlatFinalScore() != null) {
                    result.setScoreFusion(response.getFlatFinalScore());
                    result.setSeverity(response.getFlatFinalScore() > 0.8 ? "CRITICAL"
                            : (response.getFlatFinalScore() > 0.6 ? "HIGH" : "LOW"));
                    result.setConfidence(0.9);
                }

                response.setResult(result);
            }
            return response;

        } catch (Exception e) {
            log.error("Exception during ML service call", e);
            throw e;
        }
    }

    private PredictionResponseDto createFallbackResponse(String entityId) {
        PredictionResponseDto response = new PredictionResponseDto();
        response.setEntityId(entityId);
        response.setRequestId("fallback-" + UUID.randomUUID());

        PredictionResponseDto.AnomalyScoreResult result = new PredictionResponseDto.AnomalyScoreResult();
        result.setAnomaly(false);
        result.setSeverity("LOW");
        result.setScoreFusion(0.0);
        result.setConfidence(0.0);

        response.setResult(result);
        return response;
    }
}
