package com.api.monitoring.backend.service;

import com.api.monitoring.backend.dto.LogEntryRequest;
import com.api.monitoring.backend.dto.AnomalyResponse;
import com.api.monitoring.backend.dto.LogDTO;
import com.api.monitoring.backend.dto.ml.PredictionResponseDto;
import com.api.monitoring.backend.dto.ml.PredictionWindowDto;
import com.api.monitoring.backend.model.AnomalyRecord;
import com.api.monitoring.backend.model.MetricRecord;
import com.api.monitoring.backend.model.TraceRecord;
import com.api.monitoring.backend.repository.AnomalyRepository;
import com.api.monitoring.backend.repository.LogRepository;
import com.api.monitoring.backend.repository.MetricRepository;
import com.api.monitoring.backend.repository.TraceRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class MultimodalDataAggregator {

    private final MetricRepository metricRepository;
    private final LogRepository logRepository;
    private final TraceRepository traceRepository;
    private final AnomalyRepository anomalyRepository;
    private final OpenSearchLogService logService;

    public PredictionWindowDto aggregateWindow(String serviceName, Instant windowStart, Instant windowEnd) {

        List<LogDTO> logRecords = logService.getLogsByServiceAndTimeRange(serviceName, windowStart, windowEnd);

        List<PredictionWindowDto.LogEvent> logs = logRecords.stream()
                .map(l -> PredictionWindowDto.LogEvent.builder()
                        .timestamp(l.getTimestamp().toEpochMilli())
                        .level(l.getLevel())
                        .message(l.getMessage())
                        .service(l.getServiceName())
                        .build())
                .collect(Collectors.toList());

        List<MetricRecord> metricsRaw = metricRepository.findAll().stream()
                .filter(m -> isTimeInRange(m.getMetricTimestamp(), windowStart, windowEnd))
                .filter(m -> serviceName.equals(m.getServiceName()))
                .collect(Collectors.toList());

        Map<String, List<Double>> metricMap = new HashMap<>();
        metricMap.put("cpu", extract(metricsRaw, MetricRecord::getCpuUsagePercent));
        metricMap.put("memory", extract(metricsRaw, MetricRecord::getMemoryUsagePercent));
        metricMap.put("latency", extract(metricsRaw, MetricRecord::getResponseTimeMs));
        metricMap.put("error_rate", extract(metricsRaw, MetricRecord::getErrorRate));

        List<PredictionWindowDto.MetricSeries> metrics = metricMap.entrySet().stream()
                .map(e -> PredictionWindowDto.MetricSeries.builder().name(e.getKey()).values(e.getValue()).build())
                .collect(Collectors.toList());

        List<TraceRecord> tracesRaw = traceRepository.findAll().stream()
                .filter(t -> isTimeInRange(t.getStartTime(), windowStart, windowEnd))
                .filter(t -> serviceName.equals(t.getServiceName()))
                .collect(Collectors.toList());

        List<PredictionWindowDto.SpanEvent> traces = tracesRaw.stream()
                .map(t -> PredictionWindowDto.SpanEvent.builder()
                        .traceId(t.getTraceId())
                        .spanId(t.getSpanId())
                        .service(t.getServiceName())
                        .durationMs(t.getDuration() != null ? t.getDuration().doubleValue() : 0.0)
                        .isError(t.getStatusCode() >= 400)
                        .build())
                .collect(Collectors.toList());

        Map<String, String> context = new HashMap<>();
        context.put("service_name", serviceName);
        context.put("window_end_ms", String.valueOf(windowEnd.toEpochMilli()));

        return PredictionWindowDto.builder()
                .context(context)
                .metrics(metrics)
                .logs(logs)
                .traces(traces)
                .build();
    }

    public AnomalyResponse convertToAnomalyResponse(PredictionResponseDto ml, LogEntryRequest logEntry) {
        String serviceName = logEntry.getServiceName() != null ? logEntry.getServiceName() : logEntry.getApiName();
        PredictionResponseDto.AnomalyScoreResult res = ml.getResult();

        return AnomalyResponse.builder()
                .serviceName(serviceName)
                .endpoint(logEntry.getEndpoint())
                .status(res.isAnomaly() ? "ANOMALY" : "NORMAL")
                .finalAnomalyScore(res.getScoreFusion())
                .msifScore(res.getScoreMsif())
                .pleScore(res.getScorePle())
                .confidence(res.getConfidence())
                .fusionMethod("weighted_fusion_v2")
                .severity(res.getSeverity()) // FIXED: Direct string assignment
                .processingTimeMs(ml.getProcessingTimeMs())
                .timestamp(Instant.now().toString())
                .build();
    }

    @Transactional
    public void saveAnomalyRecord(PredictionResponseDto ml, LogEntryRequest logEntry) {
        String serviceName = logEntry.getServiceName() != null ? logEntry.getServiceName() : logEntry.getApiName();
        PredictionResponseDto.AnomalyScoreResult res = ml.getResult();

        AnomalyRecord record = AnomalyRecord.builder()
                .serviceName(serviceName)
                .endpoint(logEntry.getEndpoint())
                .method(logEntry.getMethod() != null ? logEntry.getMethod() : "UNKNOWN")
                .msifLstmScore(res.getScoreMsif())
                .pleGruScore(res.getScorePle())
                .hybridEnsembleScore(res.getScoreFusion())
                .fusionMethod("weighted_fusion_v2")
                .confidence(res.getConfidence())
                .severity(res.getSeverity()) // FIXED: Direct string assignment
                .status("ACTIVE")
                .isAcknowledged(false)
                .isFalsePositive(false)
                .isResolved(false)
                .mlServiceVersion(ml.getModelVersion())
                .mlProcessingTimeMs(ml.getProcessingTimeMs() != null ? ml.getProcessingTimeMs().longValue() : 0L)
                .createdAt(LocalDateTime.now())
                .build();

        anomalyRepository.save(record);
        log.info("💾 Saved anomaly record: service={}, score={}", serviceName, res.getScoreFusion());
    }

    private boolean isTimeInRange(LocalDateTime ldt, Instant start, Instant end) {
        if (ldt == null)
            return false;
        Instant i = ldt.toInstant(java.time.ZoneOffset.UTC);
        return !i.isBefore(start) && !i.isAfter(end);
    }

    private List<Double> extract(List<MetricRecord> list, java.util.function.Function<MetricRecord, Number> fn) {
        return list.stream().map(fn).filter(Objects::nonNull).map(Number::doubleValue).collect(Collectors.toList());
    }
}
