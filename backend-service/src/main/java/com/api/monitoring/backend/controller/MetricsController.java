package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.dto.MetricIngestionDTO;
import com.api.monitoring.backend.dto.MetricIngestDTO;
import com.api.monitoring.backend.model.MetricRecord;
import com.api.monitoring.backend.repository.MetricRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/metrics")

public class MetricsController {

    @Autowired
    private MetricRepository metricRepository;

    @PostMapping("/api/metrics")
    public ResponseEntity<MetricRecord> ingestMetric(@RequestBody MetricIngestionDTO dto) {
        MetricRecord metric = new MetricRecord();
        metric.setApiLogId(dto.getApiId());
        metric.setServiceName(dto.getServiceName() != null ? dto.getServiceName() : "default-service"); // ADD THIS
        metric.setCpuUsagePercent(dto.getCpuUsage());
        metric.setMemoryUsagePercent(dto.getMemoryUsage());
        metric.setDiskIoBytes(dto.getDiskIoBytes());
        metric.setNetworkIoBytes(dto.getNetworkIoBytes());
        metric.setResponseTimeMs(dto.getResponseTimeMs() != null ? dto.getResponseTimeMs().longValue() : null);
        metric.setRequestCount(dto.getRequestCount());
        metric.setErrorRate(dto.getErrorRate());
        metric.setMetricTimestamp(dto.getTimestamp() != null ? dto.getTimestamp() : LocalDateTime.now());
        metric.setCreatedAt(LocalDateTime.now());

        MetricRecord saved = metricRepository.save(metric);
        return ResponseEntity.ok(saved);
    }

    @PostMapping
    public ResponseEntity<Map<String, Object>> ingestMetric(@RequestBody MetricIngestDTO dto) {
        MetricRecord metric = new MetricRecord();
        metric.setApiLogId(dto.getApiId());
        metric.setServiceName(dto.getServiceName() != null ? dto.getServiceName() : "default-service"); // ADD THIS
        metric.setCpuUsagePercent(dto.getCpuUsage());
        metric.setMemoryUsagePercent(dto.getMemoryUsage());
        metric.setDiskIoBytes(dto.getDiskIoBytes()); // ADD THIS
        metric.setNetworkIoBytes(dto.getNetworkIoBytes()); // ADD THIS
        metric.setResponseTimeMs(
                dto.getResponseTimeMs() != null ? dto.getResponseTimeMs().longValue() : null);
        metric.setErrorRate(dto.getErrorRate());
        metric.setRequestCount(dto.getRequestCount());
        metric.setMetricTimestamp(dto.getTimestamp() != null ? dto.getTimestamp() : LocalDateTime.now());
        metric.setCreatedAt(LocalDateTime.now()); // ADD THIS

        MetricRecord saved = metricRepository.save(metric);

        Map<String, Object> response = new HashMap<>();
        response.put("status", "success");
        response.put("message", "Metric saved successfully");
        response.put("id", saved.getId());
        response.put("timestamp", saved.getMetricTimestamp());

        return ResponseEntity.ok(response);
    }

    @PostMapping("/batch")
    public ResponseEntity<Map<String, Object>> ingestMetricsBatch(@RequestBody List<MetricIngestDTO> metrics) {
        int saved = 0;
        int failed = 0;
        for (MetricIngestDTO dto : metrics) {
            try {
                MetricRecord metric = new MetricRecord();
                metric.setApiLogId(dto.getApiId());
                metric.setServiceName(dto.getServiceName() != null ? dto.getServiceName() : "default-service");
                metric.setCpuUsagePercent(dto.getCpuUsage());
                metric.setMemoryUsagePercent(dto.getMemoryUsage());
                metric.setDiskIoBytes(dto.getDiskIoBytes());
                metric.setNetworkIoBytes(dto.getNetworkIoBytes());
                metric.setResponseTimeMs(
                        dto.getResponseTimeMs() != null ? dto.getResponseTimeMs().longValue() : null);
                metric.setErrorRate(dto.getErrorRate());
                metric.setRequestCount(dto.getRequestCount());
                metric.setMetricTimestamp(dto.getTimestamp() != null ? dto.getTimestamp() : LocalDateTime.now());
                metric.setCreatedAt(LocalDateTime.now());

                metricRepository.save(metric);
                saved++;
            } catch (Exception e) {
                failed++;
                System.err.println("Error saving metric: " + e.getMessage());
            }
        }

        Map<String, Object> response = new HashMap<>();
        response.put("status", "success");
        response.put("message", "Batch ingestion completed");
        response.put("count", saved);
        response.put("failed", failed);

        return ResponseEntity.ok(response);
    }

    @GetMapping("/recent")
    public ResponseEntity<List<MetricRecord>> getRecentMetrics(
            @RequestParam(defaultValue = "100") int limit) {
        return ResponseEntity.ok(metricRepository.findTop100ByOrderByMetricTimestampDesc());
    }

    @GetMapping("/traffic")
    public ResponseEntity<List<Map<String, Object>>> getTrafficMetrics(
            @RequestParam(defaultValue = "50") int limit) {
        List<MetricRecord> metrics = metricRepository.findTop100ByOrderByMetricTimestampDesc();
        List<Map<String, Object>> trafficData = metrics.stream()
                .limit(Math.min(limit, metrics.size()))
                .map(m -> {
                    Map<String, Object> point = new HashMap<>();
                    point.put("timestamp", m.getMetricTimestamp() != null ? m.getMetricTimestamp().toString() : "");
                    point.put("requestsPerSec", m.getRequestCount() != null ? m.getRequestCount() : 0);
                    point.put("responseTimeMs", m.getResponseTimeMs() != null ? m.getResponseTimeMs() : 0);
                    point.put("errorRate", m.getErrorRate() != null ? m.getErrorRate() : 0.0);
                    return point;
                })
                .collect(java.util.stream.Collectors.toList());
        java.util.Collections.reverse(trafficData);
        return ResponseEntity.ok(trafficData);
    }

    @GetMapping("/api/{apiId}")
    public ResponseEntity<List<MetricRecord>> getMetricsByApiId(@PathVariable Long apiId) {
        return ResponseEntity.ok(metricRepository.findByApiLogId(apiId));
    }
}
