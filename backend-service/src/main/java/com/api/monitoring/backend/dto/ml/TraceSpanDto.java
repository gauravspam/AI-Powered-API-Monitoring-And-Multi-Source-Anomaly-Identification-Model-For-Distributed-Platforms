package com.api.monitoring.backend.dto.ml;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class TraceSpanDto {
    @JsonProperty("trace_id")
    private String traceId;

    @JsonProperty("span_id")
    private String spanId;

    @JsonProperty("parent_id")
    private String parentId;

    private String service;
    private String operation;

    @JsonProperty("duration_ms")
    private Double durationMs;

    @JsonProperty("status_code")
    private Integer statusCode;

    private Long timestamp;
}
