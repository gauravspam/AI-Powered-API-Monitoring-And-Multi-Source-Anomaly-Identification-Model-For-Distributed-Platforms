// backend/java-apis/src/main/java/com/api/monitoring/backend/dto/DashboardDTO.java

package com.api.monitoring.backend.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class DashboardDTO {
  private String timestamp; // Changed from long to String
  private MetricsDTO kpi;
  private List<AnomalyResponse> anomalies; // Changed from List<?> to List<AnomalyResponse>
  private EnvironmentSummaryDTO environment;
  private TrafficMetricsDTO traffic;
}
