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
public class EnvironmentSummaryDTO {

    @JsonProperty("total_services")
    private Integer totalServices;

    @JsonProperty("healthy_services")
    private Integer healthyServices;

    @JsonProperty("total_endpoints")
    private Integer totalEndpoints;

    @JsonProperty("avg_response_time")
    private Double avgResponseTime;

    @JsonProperty("deployments_24h")
    private Integer deployments;

    @JsonProperty("uptime_percentage")
    private Double uptimePercentage;

    @JsonProperty("active_alerts")
    private Integer activeAlerts;
}
