package com.api.monitoring.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder; // Missing import?
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder // Ensure this annotation is present!
@NoArgsConstructor
@AllArgsConstructor
public class StatisticsResponse {

    @JsonProperty("total_anomalies")
    private Long totalAnomalies;

    @JsonProperty("active_anomalies")
    private Long activeAnomalies;

    private Double accuracy;

    @JsonProperty("false_positive_rate")
    private Double falsePositiveRate;
}
