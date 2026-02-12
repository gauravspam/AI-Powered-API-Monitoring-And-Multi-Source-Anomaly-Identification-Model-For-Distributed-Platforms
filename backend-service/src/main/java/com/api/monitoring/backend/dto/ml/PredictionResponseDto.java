package com.api.monitoring.backend.dto.ml;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import java.util.List;

@Data
public class PredictionResponseDto {
    @JsonProperty("request_id")
    private String requestId;

    @JsonProperty("entity_id")
    private String entityId;

    private AnomalyScoreResult result;

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
