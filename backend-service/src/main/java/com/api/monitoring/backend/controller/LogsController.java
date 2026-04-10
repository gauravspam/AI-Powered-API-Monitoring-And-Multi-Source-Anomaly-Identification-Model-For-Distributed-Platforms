package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.dto.LogDTO;
import com.api.monitoring.backend.service.OpenSearchLogService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/logs")
public class LogsController {

    @Autowired
    private OpenSearchLogService logService;

    @PostMapping
    public ResponseEntity<Map<String, Object>> ingestLog(@RequestBody LogDTO logDTO) {
        if (logDTO.getTimestamp() == null) {
            logDTO.setTimestamp(Instant.now());
        }
        
        // Index to OpenSearch via Fluentd or direct
        String logId = logService.indexLog(logDTO);
        
        Map<String, Object> response = new HashMap<>();
        response.put("status", "success");
        response.put("message", "Log ingested successfully");
        response.put("logId", logId);
        
        return ResponseEntity.ok(response);
    }

    @PostMapping("/batch")
    public ResponseEntity<Map<String, Object>> ingestLogsBatch(@RequestBody List<LogDTO> logs) {
        int indexed = 0;
        for (LogDTO log : logs) {
            if (log.getTimestamp() == null) {
                log.setTimestamp(Instant.now());
            }
            logService.indexLog(log);
            indexed++;
        }
        
        Map<String, Object> response = new HashMap<>();
        response.put("status", "success");
        response.put("message", "Batch logs ingestion completed");
        response.put("count", indexed);
        
        return ResponseEntity.ok(response);
    }

    @GetMapping("/recent")
    public ResponseEntity<List<LogDTO>> getRecentLogs(
            @RequestParam(defaultValue = "100") int limit) {
        List<LogDTO> logs = logService.getRecentLogs(limit);
        return ResponseEntity.ok(logs);
    }

    @GetMapping("/search")
    public ResponseEntity<List<LogDTO>> searchLogs(
            @RequestParam String query,
            @RequestParam(defaultValue = "100") int limit) {
        List<LogDTO> logs = logService.searchLogs(query, limit);
        return ResponseEntity.ok(logs);
    }

    @GetMapping("/service/{serviceName}")
    public ResponseEntity<List<LogDTO>> getLogsByService(
            @PathVariable String serviceName,
            @RequestParam(defaultValue = "100") int limit) {
        List<LogDTO> logs = logService.getLogsByService(serviceName, limit);
        return ResponseEntity.ok(logs);
    }

    @GetMapping("/level/{level}")
    public ResponseEntity<List<LogDTO>> getLogsByLevel(
            @PathVariable String level,
            @RequestParam(defaultValue = "100") int limit) {
        List<LogDTO> logs = logService.getLogsByLevel(level, limit);
        return ResponseEntity.ok(logs);
    }

    @GetMapping("/events")
    public ResponseEntity<List<LogDTO>> getLogEvents(
            @RequestParam(defaultValue = "100") int limit) {
        return ResponseEntity.ok(logService.getRecentLogs(limit));
    }

    @GetMapping("/streams")
    public ResponseEntity<List<Map<String, Object>>> getLogStreams(
            @RequestParam(defaultValue = "20") int limit) {
        List<LogDTO> recent = logService.getRecentLogs(200);
        Map<String, Map<String, Object>> streamMap = new LinkedHashMap<>();
        for (LogDTO log : recent) {
            String svcKey = log.getServiceName() != null && !log.getServiceName().isBlank()
                ? log.getServiceName() : "unknown";
            streamMap.computeIfAbsent(svcKey, k -> {
                Map<String, Object> s = new HashMap<>();
                s.put("id", k);
                s.put("serviceName", k);
                s.put("status", "active");
                s.put("source", "fluentd");
                s.put("environment", log.getEnvironment() != null ? log.getEnvironment() : "production");
                s.put("ingestionLagSec", 0.0);
                return s;
            });
        }
        return ResponseEntity.ok(new ArrayList<>(streamMap.values()));
    }
}
