package com.api.monitoring.backend.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class TrafficMetricsDTO {
  private int current; // current RPS
  private int peak; // peak RPS
  private int average; // avg RPS
  private int percentileP95; // P95 RPS
  private String trend; // "UP", "DOWN", "STABLE"
}
