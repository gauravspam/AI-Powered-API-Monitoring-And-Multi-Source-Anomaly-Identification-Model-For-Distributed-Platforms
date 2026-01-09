package com.api.monitoring.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
public class MetricsDTO {
    private Long id;
    private String endpoint;
    private String method;
    private Integer statusCode;
    private Long responseTimeMs;
    private Integer requestCount;
    private LocalDateTime timestamp;
}