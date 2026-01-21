package com.api.monitoring.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Response DTO from Python ML Service /predict endpoint
 * Maps directly to Flask API response structure
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class MLPredictionResponse {

    @JsonProperty("msif_score")
    private Double msifScore;

    @JsonProperty("ple_score")
    private Double pleScore;

    @JsonProperty("hybrid_score")
    private Double hybridScore;

    @JsonProperty("severity")
    private String severity;

    @JsonProperty("confidence")
    private String confidence; // Can be "HIGH", "MEDIUM", "LOW"

    @JsonProperty("fusion_method")
    private String fusionMethod;

    @JsonProperty("weights_used")
    private Map<String, Double> weightsUsed;

    @JsonProperty("models_loaded")
    private Boolean modelsLoaded;

    @JsonProperty("processing_time_ms")
    private Double processingTimeMs;

    @JsonProperty("trace_id")
    private String traceId;

    /**
     * Convert confidence string to double value
     * Used by MLServiceClient for numeric confidence
     */
    public Double getConfidenceValue() {
        if (confidence == null) return 0.5;
        switch (confidence.toUpperCase()) {
            case "HIGH":
                return 0.9;
            case "MEDIUM":
                return 0.6;
            case "LOW":
                return 0.3;
            default:
                return 0.5;
        }
    }
}
