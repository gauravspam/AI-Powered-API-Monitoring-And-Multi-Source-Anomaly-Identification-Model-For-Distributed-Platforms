package com.api.monitoring.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MultimodalResponse {

    private String status;

    @JsonProperty("final_score")
    private Double finalScore;

    @JsonProperty("msif_score")
    private Double msifScore;

    @JsonProperty("ple_score")
    private Double pleScore;

    @JsonProperty("fusion_method")
    private String fusionMethod;

    @JsonProperty("model_agreement")
    private Double modelAgreement;

    private String confidence;

    @JsonProperty("modalities_present")
    private Map<String, Boolean> modalities;

    @JsonProperty("processing_time_ms")
    private Double processingTimeMs;

    @JsonProperty("model_version")
    private String modelVersion;

    private List<String> warnings;
}
