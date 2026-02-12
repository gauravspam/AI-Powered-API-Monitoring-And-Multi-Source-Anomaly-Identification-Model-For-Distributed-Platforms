package com.api.monitoring.backend.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class MetricIngestionDTO {

    @JsonAlias("api_log_id")
    private Long apiId;

    @JsonAlias("service_name")
    private String serviceName;

    @JsonAlias("cpu_usage")
    private Double cpuUsage;

    @JsonAlias("memory_usage")
    private Double memoryUsage;

    @JsonAlias("disk_io_bytes")
    private Long diskIoBytes;

    @JsonAlias("network_io_bytes")
    private Long networkIoBytes;

    @JsonAlias("response_time_ms")
    private Double responseTimeMs;

    @JsonAlias("request_count")
    private Integer requestCount;

    @JsonAlias("error_rate")
    private Double errorRate;

    private LocalDateTime timestamp;
}
