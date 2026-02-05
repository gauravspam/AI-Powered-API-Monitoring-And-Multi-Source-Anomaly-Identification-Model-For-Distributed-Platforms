package com.api.monitoring.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ErrorResponse {

    private String error;
    private String message;

    @JsonProperty("trace_id")
    private String traceId;

    private Long timestamp;

    @JsonProperty("error_code")
    private String errorCode;
}
