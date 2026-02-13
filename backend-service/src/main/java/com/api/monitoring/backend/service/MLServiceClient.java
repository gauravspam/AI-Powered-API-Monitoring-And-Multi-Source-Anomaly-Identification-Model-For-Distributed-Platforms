package com.api.monitoring.backend.service;

import com.api.monitoring.backend.dto.ml.*;
import com.api.monitoring.backend.model.LogRecord;
import com.api.monitoring.backend.model.MetricRecord;
import com.api.monitoring.backend.model.TraceRecord;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class MLServiceClient {

    private final RestTemplate restTemplate;

    @Value("${ml.service.url:http://localhost:9000}")
    private String mlServiceUrl;

    /**
     * Detect anomaly using Multimodal ML Service V2.
     * Calls POST /v1/predict with the strictly typed PredictionWindow schema.
     */
    public PredictionResponseDto detectAnomaly(
            List<MetricRecord> metrics,
            List<LogRecord> logs,
            List<TraceRecord> traces,
            String serviceName,
            Instant windowStart,
            Instant windowEnd) {

        try {
            // 1. Build the V2 Prediction Window
            PredictionWindowDto request = buildPredictionWindow(
                    metrics, logs, traces,
                    serviceName, windowStart, windowEnd);

            // 2. Prepare Endpoint
            String url = mlServiceUrl + "/v1/predict";
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<PredictionWindowDto> entity = new HttpEntity<>(request, headers);

            log.info("Calling ML Service V2: {} (Metrics: {}, Logs: {}, Traces: {})",
                    url,
                    request.getMetrics().size(),
                    request.getLogs().size(),
                    request.getTraces().size());

            // 3. Execute
            PredictionResponseDto response = restTemplate.postForObject(
                    url,
                    entity,
                    PredictionResponseDto.class);

            if (response != null && response.getResult() != null) {
                log.info("ML V2 Prediction: IsAnomaly={}, Severity={}, FusionScore={}",
                        response.getResult().isAnomaly(),
                        response.getResult().getSeverity(),
                        response.getResult().getScoreFusion());
            }

            return response;

        } catch (Exception e) {
            log.error("ML Service V2 call failed: {}", e.getMessage());
            return createFallbackResponse(serviceName, windowEnd);
        }
    }

    /**
     * Assembles the PredictionWindowDto from raw DB entities.
     * Pivots row-based MetricRecords into column-based Map<String, List<Point>>.
     */
    private PredictionWindowDto buildPredictionWindow(
            List<MetricRecord> metrics,
            List<LogRecord> logs,
            List<TraceRecord> traces,
            String serviceName,
            Instant windowStart,
            Instant windowEnd) {

        return PredictionWindowDto.builder()
                .windowStart(windowStart.toEpochMilli())
                .windowEnd(windowEnd.toEpochMilli())
                .entityId(serviceName)
                .metrics(pivotMetrics(metrics))
                .logs(mapLogs(logs))
                .traces(mapTraces(traces))
                .build();
    }

    /**
     * Pivots List<MetricRecord> (Row-based) to Map<MetricName, List<Point>>
     * (Columnar).
     */
    private Map<String, List<MetricPointDto>> pivotMetrics(List<MetricRecord> metrics) {
        if (metrics == null || metrics.isEmpty()) {
            return Collections.emptyMap();
        }

        Map<String, List<MetricPointDto>> result = new HashMap<>();
        List<MetricPointDto> cpuPoints = new ArrayList<>();
        List<MetricPointDto> memPoints = new ArrayList<>();
        List<MetricPointDto> respPoints = new ArrayList<>();

        for (MetricRecord record : metrics) {
            long ts = record.getCreatedAt().toInstant(java.time.ZoneOffset.UTC).toEpochMilli();

            if (record.getCpuUsagePercent() != null) {
                cpuPoints.add(MetricPointDto.builder().timestamp(ts).value(record.getCpuUsagePercent()).build());
            }
            if (record.getMemoryUsagePercent() != null) {
                memPoints.add(MetricPointDto.builder().timestamp(ts).value(record.getMemoryUsagePercent()).build());
            }
            if (record.getResponseTimeMs() != null) {
                respPoints.add(
                        MetricPointDto.builder().timestamp(ts).value(record.getResponseTimeMs().doubleValue()).build());
            }
        }

        result.put("cpu_usage", cpuPoints);
        result.put("memory_usage", memPoints);
        result.put("response_time", respPoints);

        return result;
    }

    private List<LogEventDto> mapLogs(List<LogRecord> logs) {
        if (logs == null)
            return Collections.emptyList();

        return logs.stream().map(log -> LogEventDto.builder()
                .timestamp(log.getCreatedAt().toInstant(java.time.ZoneOffset.UTC).toEpochMilli())
                .level(determineLogLevel(log.getStatusCode()))
                .message(log.getEndpoint() != null ? log.getEndpoint() : "unknown")
                .template_id(log.getServiceName())
                .build()).collect(Collectors.toList());
    }

    private List<TraceSpanDto> mapTraces(List<TraceRecord> traces) {
        if (traces == null)
            return Collections.emptyList();

        return traces.stream().map(t -> TraceSpanDto.builder()
                .traceId(t.getTraceId())
                .spanId(t.getSpanId())
                .parentId(t.getParentSpanId())
                .service(t.getServiceName())
                .operation(t.getOperationName())
                .durationMs(t.getDuration() != null ? t.getDuration().doubleValue() : 0.0)
                .statusCode(t.getStatusCode())
                .timestamp(t.getCreatedAt().toInstant(java.time.ZoneOffset.UTC).toEpochMilli())
                .build()).collect(Collectors.toList());
    }

    private String determineLogLevel(Integer statusCode) {
        if (statusCode == null)
            return "INFO";
        if (statusCode >= 500)
            return "ERROR";
        if (statusCode >= 400)
            return "WARN";
        return "INFO";
    }

    private PredictionResponseDto createFallbackResponse(String entityId, Instant windowEnd) {
        PredictionResponseDto response = new PredictionResponseDto();
        response.setEntityId(entityId);
        response.setRequestId("fallback-" + UUID.randomUUID());

        PredictionResponseDto.AnomalyScoreResult result = new PredictionResponseDto.AnomalyScoreResult();
        result.setAnomaly(false);
        result.setSeverity(0.0);
        result.setScoreFusion(0.0);
        result.setConfidence(0.0);

        response.setResult(result);
        return response;
    }
}
