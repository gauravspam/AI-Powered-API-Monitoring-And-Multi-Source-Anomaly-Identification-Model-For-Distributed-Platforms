package com.api.monitoring.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
public class DashboardDTO {
    private List<AnomalyDTO> recentAnomalies;
    private List<MetricsDTO> recentMetrics;
    private Integer totalAnomaliesLast24h;
    private Integer criticalCount;
    private Integer highCount;
    private Double avgResponseTime;
    private Integer errorCount;
    private Long lastUpdated;
}
