package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.dto.TraceDTO;
import com.api.monitoring.backend.model.TraceRecord;
import com.api.monitoring.backend.repository.TraceRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
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

    @Autowired
    private TraceRepository traceRepository;

    @Autowired
    private ObjectMapper objectMapper;

    @PostMapping
    @Transactional
    public ResponseEntity<Map<String, Object>> ingestTrace(@RequestBody TraceDTO traceDTO) {

        TraceRecord trace = convertToEntity(traceDTO);

        TraceRecord saved = traceRepository.save(trace);

        traceRepository.flush();

        Map<String, Object> response = new HashMap<>();
        response.put("status", "success");
        response.put("message", "Trace saved successfully");
        response.put("traceId", saved.getTraceId());

        return ResponseEntity.ok(response);
    }

    @PostMapping("/batch")
    @Transactional
    public ResponseEntity<Map<String, Object>> ingestTracesBatch(@RequestBody List<TraceDTO> traceDTOs) {
        List<TraceRecord> traces = traceDTOs.stream()
                .map(this::convertToEntity)
                .collect(Collectors.toList());

        traceRepository.saveAll(traces);
        traceRepository.flush();

        Map<String, Object> response = new HashMap<>();
        response.put("status", "success");
        response.put("message", "Batch traces ingestion completed");
        response.put("count", traceDTOs.size());

        return ResponseEntity.ok(response);
    }

    @GetMapping("/recent")
    public ResponseEntity<List<TraceDTO>> getRecentTraces(
            @RequestParam(defaultValue = "10") int limit,
            @RequestParam(defaultValue = "0") int page) {

        Pageable pageable = PageRequest.of(page, limit, Sort.by(Sort.Direction.DESC, "timestamp"));
        List<TraceRecord> traces = traceRepository.findAllByOrderByTimestampDesc(pageable);

        List<TraceDTO> dtos = traces.stream()
                .map(this::convertToDTO)
                .collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }

    @GetMapping("/{traceId}")
    public ResponseEntity<TraceDTO> getTraceById(@PathVariable String traceId) {
        Optional<TraceRecord> trace = traceRepository.findByTraceId(traceId);
        return trace.map(t -> ResponseEntity.ok(convertToDTO(t)))
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/service/{serviceName}")
    public ResponseEntity<List<TraceDTO>> getTracesByService(
            @PathVariable String serviceName,
            @RequestParam(defaultValue = "50") int limit) {

        Pageable pageable = PageRequest.of(0, limit, Sort.by(Sort.Direction.DESC, "timestamp"));
        List<TraceRecord> traces = traceRepository.findByServiceNameOrderByTimestampDesc(serviceName, pageable);

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
            @RequestParam(defaultValue = "50") int limit) {

        Pageable pageable = PageRequest.of(0, limit, Sort.by(Sort.Direction.DESC, "timestamp"));
        List<TraceRecord> traces;

        if (serviceName != null && !serviceName.isEmpty()) {
            traces = traceRepository.findByServiceNameOrderByTimestampDesc(serviceName, pageable);
        } else {
            traces = traceRepository.findAllByOrderByTimestampDesc(pageable);
        }

        if (startTime != null || endTime != null) {
            LocalDateTime start = startTime != null ? LocalDateTime.parse(startTime) : LocalDateTime.MIN;
            LocalDateTime end = endTime != null ? LocalDateTime.parse(endTime) : LocalDateTime.MAX;

            traces = traces.stream()
                    .filter(t -> {
                        LocalDateTime ts = t.getTimestamp();
                        return (ts.isEqual(start) || ts.isAfter(start)) && (ts.isEqual(end) || ts.isBefore(end));
                    })
                    .collect(Collectors.toList());
        }

        List<TraceDTO> dtos = traces.stream()
                .map(this::convertToDTO)
                .collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }

    @GetMapping("/service/{serviceName}/stats")
    public ResponseEntity<Map<String, Object>> getServiceStats(@PathVariable String serviceName) {
        Long count = traceRepository.countByServiceName(serviceName);
        Double avgDuration = traceRepository.averageDurationByServiceName(serviceName);

        Map<String, Object> stats = new HashMap<>();
        stats.put("serviceName", serviceName);
        stats.put("totalTraces", count != null ? count : 0);
        stats.put("averageDurationMs", avgDuration != null ? avgDuration : 0.0);

        return ResponseEntity.ok(stats);
    }

    private TraceRecord convertToEntity(TraceDTO dto) {
        TraceRecord trace = new TraceRecord();
        trace.setTraceId(dto.getTraceId());
        trace.setSpanId(dto.getSpanId());
        trace.setParentSpanId(dto.getParentSpanId());
        trace.setServiceName(dto.getServiceName());
        trace.setOperationName(dto.getOperationName());
        trace.setDuration(dto.getDuration() != null ? dto.getDuration().longValue() : null);
        trace.setStatusCode(dto.getStatusCode());

        if (dto.getTimestamp() != null) {
            trace.setTimestamp(LocalDateTime.ofInstant(dto.getTimestamp(), ZoneOffset.UTC));
        } else {
            trace.setTimestamp(LocalDateTime.now(ZoneOffset.UTC));
        }

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

        // Fixed: proper null handling for Long to Integer conversion
        if (trace.getDuration() != null) {
            dto.setDuration(trace.getDuration());
        }

        dto.setStatusCode(trace.getStatusCode());

        if (trace.getTimestamp() != null) {
            dto.setTimestamp(trace.getTimestamp().toInstant(ZoneOffset.UTC));
        }

        if (trace.getTags() != null && !trace.getTags().isEmpty()) {
            try {
                dto.setTags(objectMapper.readValue(trace.getTags(), Map.class));
            } catch (JsonProcessingException e) {
                dto.setTags(new HashMap<>());
            }
        }

        return dto;
    }
}
