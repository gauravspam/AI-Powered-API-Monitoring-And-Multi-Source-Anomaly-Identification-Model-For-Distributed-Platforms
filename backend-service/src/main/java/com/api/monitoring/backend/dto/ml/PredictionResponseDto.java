package com.api.monitoring.backend.dto.ml;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class PredictionResponseDto {
    @JsonProperty("request_id")
    private String requestId;

    @JsonProperty("entity_id")
    private String entityId;

    @JsonProperty("window_end")
    private Long windowEnd;

    private AnomalyScoreResult result;

    @JsonProperty("processing_time_ms")
    private Double processingTimeMs;

    @JsonProperty("model_version")
    private String modelVersion;

    @Data
    public static class AnomalyScoreResult {
        @JsonProperty("is_anomaly")
        private boolean isAnomaly;

        private double severity;

        @JsonProperty("score_msif")
        private double scoreMsif;

        @JsonProperty("score_ple")
        private double scorePle;

        @JsonProperty("score_fusion")
        private double scoreFusion;

        private double confidence;
    }
}
