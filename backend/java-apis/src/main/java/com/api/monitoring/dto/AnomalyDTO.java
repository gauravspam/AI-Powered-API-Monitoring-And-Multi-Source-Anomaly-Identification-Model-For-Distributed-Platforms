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
public class AnomalyDTO {
    private Long id;
    private String apiEndpoint;
    private String method;
    private String anomalyType;
    private Float score;
    private String severity;
    private LocalDateTime timestamp;
}
