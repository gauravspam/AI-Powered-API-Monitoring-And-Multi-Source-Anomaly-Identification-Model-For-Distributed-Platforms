package com.api.monitoring.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AnomalyResponse {

    @JsonProperty("service_name")
    private String serviceName;

    private String endpoint;

    private String status;
    private String severity;
    private Double confidence;

    @JsonProperty("final_score")
    private Double finalAnomalyScore;

    @JsonProperty("msif_score")
    private Double msifScore;

    @JsonProperty("ple_score")
    private Double pleScore;

    @JsonProperty("fusion_method")
    private String fusionMethod;

    @JsonProperty("processing_time_ms")
    private Double processingTimeMs;

    private String timestamp;

    // Legacy support
    @JsonProperty("api_name")
    public String getApiName() {
        return serviceName;
    }

    public void setApiName(String apiName) {
        this.serviceName = apiName;
    }
}
