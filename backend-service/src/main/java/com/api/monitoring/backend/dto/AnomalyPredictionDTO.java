package com.api.monitoring.backend.dto;

import java.time.LocalDateTime;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO for ML anomaly prediction results
 * Returned by MLServiceClient after calling Python ML service
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AnomalyPredictionDTO {

    private Long logId;
    private String endpoint;
    private String method;

    // ML Scores
    private Double msifScore;
    private Double pleScore;
    private Double hybridScore;

    // Analysis results
    private String severity;
    private Double confidence;
    private String fusionMethod;

    // Metadata
    private Long mlProcessingTimeMs;
    private String mlServiceVersion;
    private String traceId;
    private LocalDateTime timestamp;
}
