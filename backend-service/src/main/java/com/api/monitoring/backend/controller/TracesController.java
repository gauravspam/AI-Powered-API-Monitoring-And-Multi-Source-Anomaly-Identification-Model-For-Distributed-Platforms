package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.dto.TraceDTO;
import com.api.monitoring.backend.model.TraceRecord;
import com.api.monitoring.backend.repository.TraceRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/traces")
public class TracesController {

    private final TraceRepository traceRepository;
    private final ObjectMapper objectMapper;

    @Autowired
    public TracesController(TraceRepository traceRepository, ObjectMapper objectMapper) {
        this.traceRepository = traceRepository;
        this.objectMapper = objectMapper;
    }

    @PostMapping("/ingest")
    @Transactional
    public ResponseEntity<Map<String, Object>> ingestTrace(@RequestBody TraceDTO traceDTO) {
        TraceRecord trace = convertToEntity(traceDTO);
        TraceRecord saved = traceRepository.save(trace);
        traceRepository.flush();

        Map<String, Object> response = new HashMap<>();
        response.put("id", saved.getId());
        response.put("traceId", saved.getTraceId());
        response.put("status", "success");
        response.put("message", "Trace ingested successfully");

        return ResponseEntity.ok(response);
    }

    @PostMapping("/ingest/batch")
    @Transactional
    public ResponseEntity<Map<String, Object>> ingestTracesBatch(@RequestBody List<TraceDTO> traceDTOs) {
        List<TraceRecord> traces = traceDTOs.stream()
                .map(this::convertToEntity)
                .collect(Collectors.toList());

        List<TraceRecord> saved = traceRepository.saveAll(traces);
        traceRepository.flush();

        Map<String, Object> response = new HashMap<>();
        response.put("count", saved.size());
        response.put("status", "success");
        response.put("message", "Batch ingestion completed");

        return ResponseEntity.ok(response);
    }

    @GetMapping("/recent")
    public ResponseEntity<List<TraceDTO>> getRecentTraces(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "100") int size) {

        Pageable pageable = PageRequest.of(page, size);
        List<TraceRecord> traces = traceRepository.findAllByOrderByStartTimeDesc(pageable);

        List<TraceDTO> dtos = traces.stream()
                .map(this::convertToDTO)
                .collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }

    @GetMapping("/service/{serviceName}")
    public ResponseEntity<List<TraceDTO>> getTracesByService(
            @PathVariable String serviceName,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "100") int size) {

        Pageable pageable = PageRequest.of(page, size);
        List<TraceRecord> traces = traceRepository.findByServiceNameOrderByStartTimeDesc(serviceName, pageable);

        List<TraceDTO> dtos = traces.stream()
                .map(this::convertToDTO)
                .collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }

    @GetMapping("/search")
    public ResponseEntity<List<TraceDTO>> searchTraces(
            @RequestParam(required = false) String serviceName,
            @RequestParam(required = false) String startTime,
            @RequestParam(required = false) String endTime,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "100") int size) {

        Pageable pageable = PageRequest.of(page, size);
        List<TraceRecord> traces;

        if (serviceName != null && !serviceName.isBlank()) {
            traces = traceRepository.findByServiceNameOrderByStartTimeDesc(serviceName, pageable);
        } else {
            traces = traceRepository.findAllByOrderByStartTimeDesc(pageable);
        }

        // Filter by time range if provided
        if (startTime != null || endTime != null) {
            LocalDateTime start = startTime != null ? LocalDateTime.parse(startTime) : LocalDateTime.MIN;
            LocalDateTime end = endTime != null ? LocalDateTime.parse(endTime) : LocalDateTime.MAX;

            traces = traces.stream()
                    .filter(t -> {
                        LocalDateTime ts = t.getStartTime();
                        return (ts.isEqual(start) || ts.isAfter(start)) &&
                                (ts.isEqual(end) || ts.isBefore(end));
                    })
                    .collect(Collectors.toList());
        }

        List<TraceDTO> dtos = traces.stream()
                .map(this::convertToDTO)
                .collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }

    @GetMapping("/stats/{serviceName}")
    public ResponseEntity<Map<String, Object>> getServiceStats(@PathVariable String serviceName) {
        Long count = traceRepository.countByServiceName(serviceName);
        Double avgDuration = traceRepository.averageDurationByServiceName(serviceName);

        Map<String, Object> stats = new HashMap<>();
        stats.put("serviceName", serviceName);
        stats.put("totalTraces", count != null ? count : 0);
        stats.put("averageDurationMs", avgDuration != null ? avgDuration : 0.0);

        return ResponseEntity.ok(stats);
    }

    @GetMapping("/{traceId}")
    public ResponseEntity<TraceDTO> getTraceById(@PathVariable String traceId) {
        Optional<TraceRecord> trace = traceRepository.findByTraceId(traceId);
        return trace.map(this::convertToDTO)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    // ========== Conversion Methods ==========

    private TraceRecord convertToEntity(TraceDTO dto) {
        TraceRecord trace = new TraceRecord();
        trace.setTraceId(dto.getTraceId());
        trace.setSpanId(dto.getSpanId());
        trace.setParentSpanId(dto.getParentSpanId());
        trace.setServiceName(dto.getServiceName());
        trace.setOperationName(dto.getOperationName());
        trace.setDuration(dto.getDuration());
        trace.setStatusCode(dto.getStatusCode());

        // DTO uses 'timestamp' (Instant), Entity uses 'startTime' (LocalDateTime)
        if (dto.getTimestamp() != null) {
            trace.setStartTime(LocalDateTime.ofInstant(dto.getTimestamp(), ZoneOffset.UTC));
        } else {
            trace.setStartTime(LocalDateTime.now(ZoneOffset.UTC));
        }

        // Serialize tags: DTO has Map<String, String>, Entity stores as JSON String
        if (dto.getTags() != null && !dto.getTags().isEmpty()) {
            try {
                trace.setTags(objectMapper.writeValueAsString(dto.getTags()));
            } catch (JsonProcessingException e) {
                trace.setTags("{}");
            }
        }

        return trace;
    }

    private TraceDTO convertToDTO(TraceRecord trace) {
        TraceDTO dto = new TraceDTO();
        dto.setTraceId(trace.getTraceId());
        dto.setSpanId(trace.getSpanId());
        dto.setParentSpanId(trace.getParentSpanId());
        dto.setServiceName(trace.getServiceName());
        dto.setOperationName(trace.getOperationName());
        dto.setDuration(trace.getDuration());
        dto.setStatusCode(trace.getStatusCode());

        // Entity uses 'startTime' (LocalDateTime), DTO uses 'timestamp' (Instant)
        if (trace.getStartTime() != null) {
            dto.setTimestamp(trace.getStartTime().toInstant(ZoneOffset.UTC));
        }

        // Deserialize tags: Entity stores as JSON String, DTO has Map<String, String>
        if (trace.getTags() != null && !trace.getTags().isBlank()) {
            try {
                Map<String, String> tagsMap = objectMapper.readValue(
                        trace.getTags(),
                        new TypeReference<Map<String, String>>() {
                        });
                dto.setTags(tagsMap);
            } catch (JsonProcessingException e) {
                dto.setTags(new HashMap<>());
            }
        }

        return dto;
    }
}
