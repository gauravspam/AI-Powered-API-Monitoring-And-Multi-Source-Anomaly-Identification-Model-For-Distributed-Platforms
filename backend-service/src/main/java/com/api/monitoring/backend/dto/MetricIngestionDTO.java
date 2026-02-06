package com.api.monitoring.backend.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class MetricIngestionDTO {
    private Long apiId;
    private String serviceName;
    private Double cpuUsage;
    private Double memoryUsage;
    private Long diskIoBytes;
    private Long networkIoBytes;
    private Double responseTimeMs;
    private Integer requestCount;
    private Double errorRate;
    private LocalDateTime timestamp;
}
