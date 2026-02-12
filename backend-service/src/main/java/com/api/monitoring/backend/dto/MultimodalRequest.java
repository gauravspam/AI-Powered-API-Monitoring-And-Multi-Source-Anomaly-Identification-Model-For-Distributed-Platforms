package com.api.monitoring.backend.dto;

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
public class MultimodalRequest {

    private WindowContext context;
    private List<MetricSeries> metrics;
    private List<LogEvent> logs;
    private List<SpanEvent> traces;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class WindowContext {
        private String serviceName;
        private String endpoint;
        private String environment;
        private Long windowStartMs;
        private Long windowEndMs;
        private String traceId;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class MetricSeries {
        private String name;
        private List<Double> values;
        private List<Long> timestamps;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class LogEvent {
        private Long timestamp;
        private String level;
        private String template;
        private String service;
        private Map<String, String> attributes;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SpanEvent {
        private String traceId;
        private String spanId;
        private String parentSpanId;
        private String service;
        private String operation;
        private Double durationMs;
        private Integer statusCode;
        private Boolean isError;
        private Map<String, String> tags;
    }
}
