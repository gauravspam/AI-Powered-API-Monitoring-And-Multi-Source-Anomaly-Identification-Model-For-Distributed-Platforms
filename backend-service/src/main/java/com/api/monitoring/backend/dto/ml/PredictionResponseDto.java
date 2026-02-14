package com.api.monitoring.backend.dto.ml;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class PredictionResponseDto {

    @JsonProperty("request_id")
    @JsonAlias({ "requestId", "requestid" })
    private String requestId;

    @JsonProperty("entity_id")
    @JsonAlias({ "entityId", "entityid", "service_name" })
    private String entityId;

    @JsonProperty("window_end")
    @JsonAlias({ "windowEnd", "window_end_ms" })
    private Long windowEnd;

    @JsonProperty("processing_time_ms")
    @JsonAlias({ "processingTimeMs", "processingtimems" })
    private Double processingTimeMs;

    @JsonProperty("model_version")
    @JsonAlias({ "modelVersion", "modelversion" })
    private String modelVersion;

    @JsonProperty("result")
    private AnomalyScoreResult result;

    @JsonProperty("final_score")
    @JsonAlias({ "finalScore", "finalscore", "score_fusion", "scorefusion", "hybrid_score" })
    private Double flatFinalScore;

    @JsonProperty("is_anomaly")
    @JsonAlias({ "isAnomaly", "isanomaly" })
    private Boolean flatIsAnomaly;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class AnomalyScoreResult {

        @JsonProperty("is_anomaly")
        @JsonAlias({ "isAnomaly", "isanomaly" })
        private boolean isAnomaly;

        @JsonProperty("severity")
        private String severity; // MUST BE STRING

        @JsonProperty("score_fusion")
        @JsonAlias({ "scoreFusion", "scorefusion", "final_score", "hybrid_score" })
        private double scoreFusion;

        @JsonProperty("score_msif")
        @JsonAlias({ "scoreMsif", "scoremsif", "msif_score" })
        private double scoreMsif;

        @JsonProperty("score_ple")
        @JsonAlias({ "scorePle", "scoreple", "ple_score" })
        private double scorePle;

        @JsonProperty("confidence")
        @JsonAlias({ "confidence_score" })
        private double confidence;
    }
}
