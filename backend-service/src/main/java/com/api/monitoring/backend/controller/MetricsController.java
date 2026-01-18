package com.api.monitoring.backend.controller;

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

    @PostMapping
    public ResponseEntity<Map<String, Object>> ingestMetric(@RequestBody MetricIngestDTO dto) {
        MetricRecord metric = new MetricRecord();
        metric.setApiId(dto.getApiId());
        metric.setCpuUsage(dto.getCpuUsage());
        metric.setMemoryUsage(dto.getMemoryUsage());
        metric.setResponseTimeMs(dto.getResponseTimeMs());
        metric.setErrorRate(dto.getErrorRate());
        metric.setRequestCount(dto.getRequestCount());
        metric.setTimestamp(dto.getTimestamp() != null ? dto.getTimestamp() : LocalDateTime.now());
        
        MetricRecord saved = metricRepository.save(metric);
        
        Map<String, Object> response = new HashMap<>();
        response.put("status", "success");
        response.put("message", "Metric saved successfully");
        response.put("id", saved.getId());
        response.put("timestamp", saved.getTimestamp());
        
        return ResponseEntity.ok(response);
    }

    @PostMapping("/batch")
    public ResponseEntity<Map<String, Object>> ingestMetricsBatch(@RequestBody List<MetricIngestDTO> metrics) {
        int saved = 0;
        for (MetricIngestDTO dto : metrics) {
            MetricRecord metric = new MetricRecord();
            metric.setApiId(dto.getApiId());
            metric.setCpuUsage(dto.getCpuUsage());
            metric.setMemoryUsage(dto.getMemoryUsage());
            metric.setResponseTimeMs(dto.getResponseTimeMs());
            metric.setErrorRate(dto.getErrorRate());
            metric.setRequestCount(dto.getRequestCount());
            metric.setTimestamp(dto.getTimestamp() != null ? dto.getTimestamp() : LocalDateTime.now());
            
            metricRepository.save(metric);
            saved++;
        }
        
        Map<String, Object> response = new HashMap<>();
        response.put("status", "success");
        response.put("message", "Batch ingestion completed");
        response.put("count", saved);
        
        return ResponseEntity.ok(response);
    }

    @GetMapping("/recent")
    public ResponseEntity<List<MetricRecord>> getRecentMetrics(
            @RequestParam(defaultValue = "100") int limit) {
        return ResponseEntity.ok(metricRepository.findTop100ByOrderByTimestampDesc());
    }

    @GetMapping("/api/{apiId}")
    public ResponseEntity<List<MetricRecord>> getMetricsByApiId(@PathVariable Long apiId) {
        return ResponseEntity.ok(metricRepository.findByApiId(apiId));
    }
}
