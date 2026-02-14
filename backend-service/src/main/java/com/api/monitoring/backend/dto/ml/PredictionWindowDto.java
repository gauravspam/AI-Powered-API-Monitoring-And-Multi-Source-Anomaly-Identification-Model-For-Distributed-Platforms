package com.api.monitoring.backend.dto.ml;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PredictionWindowDto {

    @JsonProperty("context")
    private Map<String, String> context;

    @JsonProperty("metrics")
    private List<MetricSeries> metrics;

    @JsonProperty("logs")
    private List<LogEvent> logs;

    @JsonProperty("traces")
    private List<SpanEvent> traces;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class MetricSeries {
        private String name;
        private List<Double> values;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class LogEvent {
        private Long timestamp;
        private String level;
        private String message;
        private String service;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SpanEvent {
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
        @JsonProperty("is_error")
        private Boolean isError;
    }
}
