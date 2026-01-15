package com.api.monitoring.backend.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class MetricsDTO {
  private long totalRequests;
  private double successRate; // 0-100%
  private double errorRate; // 0-100%
  private double avgLatency; // milliseconds
  private double p95Latency; // milliseconds
  private double p99Latency; // milliseconds
  private double uptime; // 0-100%
}
