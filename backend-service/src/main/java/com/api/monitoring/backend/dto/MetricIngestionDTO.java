package com.api.monitoring.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class MetricIngestionDTO {
    private Long apiId;

    @JsonProperty("service_name")
    private String serviceName;

    @JsonProperty("cpu_usage")
    private Double cpuUsage;

    @JsonProperty("memory_usage")
    private Double memoryUsage;

    @JsonProperty("disk_io_bytes")
    private Long diskIoBytes;

    @JsonProperty("network_io_bytes")
    private Long networkIoBytes;

    @JsonProperty("response_time_ms")
    private Double responseTimeMs;

    @JsonProperty("request_count")
    private Integer requestCount;

    @JsonProperty("error_rate")
    private Double errorRate;

    private LocalDateTime timestamp;
}
