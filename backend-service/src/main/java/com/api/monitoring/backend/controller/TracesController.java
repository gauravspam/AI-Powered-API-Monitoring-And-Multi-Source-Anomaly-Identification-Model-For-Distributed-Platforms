package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.dto.TraceDTO;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.util.*;

@RestController
@RequestMapping("/api/traces")
public class TracesController {

    // In-memory storage for now (replace with repository later)
    private final List<TraceDTO> traces = Collections.synchronizedList(new ArrayList<>());

    @PostMapping
    public ResponseEntity<Map<String, Object>> ingestTrace(@RequestBody TraceDTO traceDTO) {
        if (traceDTO.getTimestamp() == null) {
            traceDTO.setTimestamp(Instant.now());
        }
        
        traces.add(traceDTO);
        
        Map<String, Object> response = new HashMap<>();
        response.put("status", "success");
        response.put("message", "Trace saved successfully");
        response.put("traceId", traceDTO.getTraceId());
        
        return ResponseEntity.ok(response);
    }

    @PostMapping("/batch")
    public ResponseEntity<Map<String, Object>> ingestTracesBatch(@RequestBody List<TraceDTO> traceDTOs) {
        for (TraceDTO trace : traceDTOs) {
            if (trace.getTimestamp() == null) {
                trace.setTimestamp(Instant.now());
            }
            traces.add(trace);
        }
        
        Map<String, Object> response = new HashMap<>();
        response.put("status", "success");
        response.put("message", "Batch traces ingestion completed");
        response.put("count", traceDTOs.size());
        
        return ResponseEntity.ok(response);
    }

    @GetMapping("/recent")
    public ResponseEntity<List<TraceDTO>> getRecentTraces(
            @RequestParam(defaultValue = "100") int limit) {
        int size = Math.min(limit, traces.size());
        return ResponseEntity.ok(traces.subList(Math.max(0, traces.size() - size), traces.size()));
    }

    @GetMapping("/{traceId}")
    public ResponseEntity<TraceDTO> getTraceById(@PathVariable String traceId) {
        return traces.stream()
                .filter(t -> t.getTraceId().equals(traceId))
                .findFirst()
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/service/{serviceName}")
    public ResponseEntity<List<TraceDTO>> getTracesByService(@PathVariable String serviceName) {
        List<TraceDTO> filtered = traces.stream()
                .filter(t -> serviceName.equals(t.getServiceName()))
                .toList();
        return ResponseEntity.ok(filtered);
    }
}
