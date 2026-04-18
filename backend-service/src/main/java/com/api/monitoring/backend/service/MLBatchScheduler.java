package com.api.monitoring.backend.service;

import com.api.monitoring.backend.dto.MLPredictionResponse;
import com.api.monitoring.backend.model.AnomalyRecord;
import com.api.monitoring.backend.model.LogRecord;
import com.api.monitoring.backend.model.MetricRecord;
import com.api.monitoring.backend.model.TraceRecord;
import com.api.monitoring.backend.repository.AnomalyRepository;
import com.api.monitoring.backend.repository.LogRepository;
import com.api.monitoring.backend.repository.MetricRepository;
import com.api.monitoring.backend.repository.TraceRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Service
@Slf4j
public class MLBatchScheduler {

    @Value("${python.service.url:http://localhost:9000}")
    private String mlServiceUrl;

    @Value("${python.service.enabled:true}")
    private boolean mlServiceEnabled;

    @Value("${app.ml.batch.enabled:true}")
    private boolean batchEnabled;

    private final RestTemplate restTemplate;
    private final LogRepository logRepository;
    private final MetricRepository metricRepository;
    private final TraceRepository traceRepository;
    private final AnomalyRepository anomalyRepository;
    private final AlertService alertService;

    @Autowired
    public MLBatchScheduler(
            RestTemplate restTemplate,
            LogRepository logRepository,
            MetricRepository metricRepository,
            TraceRepository traceRepository,
            AnomalyRepository anomalyRepository,
            AlertService alertService) {
        this.restTemplate = restTemplate;
        this.logRepository = logRepository;
        this.metricRepository = metricRepository;
        this.traceRepository = traceRepository;
        this.anomalyRepository = anomalyRepository;
        this.alertService = alertService;
    }

    @Scheduled(fixedRate = 120000) // 2 minutes
    public void processBatch() {
        if (!batchEnabled || !mlServiceEnabled) {
            log.debug("Batch processing disabled, skipping");
            return;
        }

        log.info("Starting ML batch processing...");
        long startTime = System.currentTimeMillis();

        try {
            LocalDateTime since = LocalDateTime.now().minusMinutes(2);

            List<Map<String, Object>> metrics = fetchRecentMetrics(since);
            List<Map<String, Object>> logs = fetchRecentLogs(since);
            List<Map<String, Object>> traces = fetchRecentTraces(since);

            log.info("Fetched data - Metrics: {}, Logs: {}, Traces: {}", 
                    metrics.size(), logs.size(), traces.size());

            if (metrics.isEmpty() && logs.isEmpty() && traces.isEmpty()) {
                log.info("No recent data to process");
                return;
            }

            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("metrics", metrics);
            requestBody.put("logs", logs);
            requestBody.put("traces", traces);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

            String endpoint = mlServiceUrl + "/predict/batch";
            ResponseEntity<MLPredictionResponse> response = restTemplate.exchange(
                    endpoint,
                    HttpMethod.POST,
                    request,
                    MLPredictionResponse.class
            );

            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                processPredictions(response.getBody());
            }

            long duration = System.currentTimeMillis() - startTime;
            log.info("ML batch processing completed in {}ms", duration);

        } catch (Exception e) {
            log.error("ML batch processing failed: {}", e.getMessage(), e);
        }
    }

    private List<Map<String, Object>> fetchRecentMetrics(LocalDateTime since) {
        List<MetricRecord> records = metricRepository.findByMetricTimestampAfter(since);
        return records.stream().limit(5000).map(this::convertMetricToMap).collect(Collectors.toList());
    }

    private List<Map<String, Object>> fetchRecentLogs(LocalDateTime since) {
        // For now, return empty - LogRecord doesn't have timestamp field
        // Will need to add created_at filtering
        return Collections.emptyList();
    }

    private List<Map<String, Object>> fetchRecentTraces(LocalDateTime since) {
        // For traces, use startTime field
        List<TraceRecord> records = traceRepository.findByStartTimeAfter(since);
        return records.stream().limit(5000).map(this::convertTraceToMap).collect(Collectors.toList());
    }

    private Map<String, Object> convertMetricToMap(MetricRecord record) {
        Map<String, Object> map = new HashMap<>();
        map.put("service_name", record.getServiceName());
        map.put("cpu_usage", record.getCpuUsagePercent());
        map.put("memory_usage", record.getMemoryUsagePercent());
        map.put("disk_io_bytes", record.getDiskIoBytes());
        map.put("network_io_bytes", record.getNetworkIoBytes());
        map.put("response_time_ms", record.getResponseTimeMs());
        map.put("request_count", record.getRequestCount());
        map.put("error_rate", record.getErrorRate());
        map.put("environment", record.getEnvironment());
        return map;
    }

    private Map<String, Object> convertTraceToMap(TraceRecord record) {
        Map<String, Object> map = new HashMap<>();
        map.put("trace_id", record.getTraceId());
        map.put("span_id", record.getSpanId());
        map.put("parent_span_id", record.getParentSpanId());
        map.put("service_name", record.getServiceName());
        map.put("operation_name", record.getOperationName());
        map.put("duration_ms", record.getDuration());
        map.put("status_code", record.getStatusCode());
        map.put("environment", "production");
        if (record.getTags() != null) {
            map.put("tags", record.getTags());
        }
        return map;
    }

    private void processPredictions(MLPredictionResponse response) {
        if (response.getPredictions() == null) {
            return;
        }

        for (var pred : response.getPredictions()) {
            double score = pred.getFinalScore();
            
            if (score >= 0.6) {
                AnomalyRecord anomaly = AnomalyRecord.builder()
                        .endpoint("batch-" + pred.getIndex())
                        .msifLstmScore(pred.getMsifScore())
                        .pleGruScore(pred.getPleScore())
                        .hybridEnsembleScore(score)
                        .confidence(pred.getConfidence())
                        .severity(determineSeverity(score))
                        .fusionMethod("batch-ensemble")
                        .status("ACTIVE")
                        .createdAt(LocalDateTime.now())
                        .build();
                
                anomalyRepository.save(anomaly);
                log.info("Saved anomaly with score: {}", score);

                if (score >= 0.8) {
                    alertService.triggerAlert(anomaly);
                }
            }
        }
    }

    private String determineSeverity(double score) {
        if (score >= 0.85) return "CRITICAL";
        if (score >= 0.70) return "HIGH";
        if (score >= 0.50) return "MEDIUM";
        return "LOW";
    }
}