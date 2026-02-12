package com.api.monitoring.backend.model;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

@Entity
@Table(name = "system_metrics")
@Data
public class MetricRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "api_log_id")
    private Long apiLogId;

    @Column(name = "service_name", nullable = false)
    private String serviceName;

    @Column(name = "endpoint")
    private String endpoint;

    @Column(name = "cpu_usage_percent")
    private Double cpuUsagePercent;

    @Column(name = "memory_usage_percent")
    private Double memoryUsagePercent;

    @Column(name = "disk_io_bytes")
    private Long diskIoBytes; // Added

    @Column(name = "network_io_bytes")
    private Long networkIoBytes; // Added

    @Column(name = "response_time_ms")
    private Long responseTimeMs;

    @Column(name = "request_count")
    private Integer requestCount;

    @Column(name = "error_rate")
    private Double errorRate;

    @Column(name = "metric_timestamp", nullable = false)
    private LocalDateTime metricTimestamp;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        if (createdAt == null)
            createdAt = LocalDateTime.now();
        if (metricTimestamp == null)
            metricTimestamp = LocalDateTime.now();
        if (serviceName == null)
            serviceName = "default-service";
    }
}
