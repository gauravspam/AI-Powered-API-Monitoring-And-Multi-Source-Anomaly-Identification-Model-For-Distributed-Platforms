package com.api.monitoring.backend.dto.ml;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Data;
import java.util.List;
import java.util.Map;

@Data
@Builder
public class PredictionWindowDto {
    @JsonProperty("window_start")
    private Long windowStart;

    @JsonProperty("window_end")
    private Long windowEnd;

    @JsonProperty("entity_id")
    private String entityId;

    private Map<String, List<MetricPointDto>> metrics;
    private List<LogEventDto> logs;
    private List<TraceSpanDto> traces;
}

@Data
@Builder
public class MetricPointDto {
    private Long timestamp;
    private Double value;
}

@Data
@Builder
public class LogEventDto {
    private Long timestamp;
    private String level;
    private String message;
    private String template_id;
}

@Data
@Builder
public class TraceSpanDto {
    @JsonProperty("trace_id")
    private String traceId;
    @JsonProperty("span_id")
    private String spanId;
    private String service;
    private String operation;
    @JsonProperty("duration_ms")
    private Double durationMs;
    @JsonProperty("status_code")
    private Integer statusCode;
    private Long timestamp;
}
