package com.api.monitoring.backend.dto;

import java.time.LocalDateTime;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import com.fasterxml.jackson.annotation.JsonProperty;

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

    // Analysis results
    private String severity;
    private Double confidence;
    private String fusionMethod;

    // Metadata
    private Long mlProcessingTimeMs;
    private String mlServiceVersion;
    private String traceId;
    private LocalDateTime timestamp;

    @JsonProperty("hybrid_score") // ← Maps Python's snake_case
    private Double hybridScore;

    @JsonProperty("msif_lstm_score")
    private Double msifLstmScore;

    @JsonProperty("ple_gru_score")
    private Double pleGruScore;

    @JsonProperty("anomaly_details")
    private String anomalyDetails;

}
