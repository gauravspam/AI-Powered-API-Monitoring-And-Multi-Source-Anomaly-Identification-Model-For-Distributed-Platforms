package com.api.monitoring.backend.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class EnvironmentSummaryDTO {
  private int totalServices;
  private int healthyServices;
  private int totalEndpoints;
  private double avgResponseTime;
  private int deployments;
  private double uptimePercentage;
}
