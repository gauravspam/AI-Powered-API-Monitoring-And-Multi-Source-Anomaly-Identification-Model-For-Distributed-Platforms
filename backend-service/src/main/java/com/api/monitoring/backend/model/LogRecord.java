package com.api.monitoring.backend.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.Map;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;
import lombok.ToString;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Table(name = "api_logs", indexes = { 
        @Index(name = "idx_api_logs_endpoint", columnList = "endpoint"),
        @Index(name = "idx_api_logs_status_code", columnList = "status_code"),
        @Index(name = "idx_api_logs_created_at", columnList = "created_at DESC"),
        @Index(name = "idx_api_logs_trace_id", columnList = "trace_id")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@EqualsAndHashCode(of = "id")
@ToString(exclude = { "requestBody", "responseBody", "requestHeaders", "responseHeaders", "metadata" })
public class LogRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "endpoint", nullable = false, length = 500)
    private String endpoint;

    @Column(name = "http_method", nullable = false, length = 10)
    private String method;

    @Column(name = "status_code", nullable = false)
    private Integer statusCode;

    @Column(name = "response_time_ms", nullable = false)
    private Long responseTimeMs;

    @Column(name = "request_size_bytes")
    private Long requestSizeBytes;

    @Column(name = "response_size_bytes")
    private Long responseSizeBytes;

    @Column(name = "cpu_usage_percent")
    private Double cpuUsage;

    @Column(name = "memory_usage_percent")
    private Double memoryUsage;

    @Column(name = "disk_io_bytes")
    private Long diskIo;

    @Column(name = "network_io_bytes")
    private Long networkIo;

    @Column(name = "error_rate")
    private Double errorRate;

    @Column(name = "error_count")
    private Integer errorCount;

    @Column(name = "error_message", columnDefinition = "TEXT")
    private String errorMessage;

    @Column(name = "stack_trace", columnDefinition = "TEXT")
    private String stackTrace;

    @Column(name = "request_count")
    private Integer requestCount;

    @Column(name = "user_id")
    private String userId;

    @Column(name = "ip_address", columnDefinition = "inet")
    private String ipAddress;

    @Column(name = "user_agent", columnDefinition = "TEXT")
    private String userAgent;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "request_body", columnDefinition = "jsonb")
    private Map<String, Object> requestBody;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "response_body", columnDefinition = "jsonb")
    private Map<String, Object> responseBody;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "request_headers", columnDefinition = "jsonb")
    private Map<String, Object> requestHeaders;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "response_headers", columnDefinition = "jsonb")
    private Map<String, Object> responseHeaders;

    @Column(name = "trace_id")
    private String traceId;

    @Column(name = "span_id")
    private String spanId;

    @Column(name = "parent_span_id")
    private String parentSpanId;

    @Column(name = "service_name", nullable = false)
    private String serviceName;

    @Column(name = "service_version")
    private String serviceVersion;

    @Builder.Default
    @Column(name = "environment")
    private String environment = "production";

    @Column(name = "hour_of_day")
    private Integer hourOfDay;

    @Column(name = "day_of_week")
    private Integer dayOfWeek;

    @Column(name = "is_weekend")
    private Boolean isWeekend;

    @Column(name = "is_business_hours")
    private Boolean isBusinessHours;

    @Builder.Default
    @Column(name = "is_processed", nullable = false)
    private Boolean isProcessed = false;

    @Column(name = "processed_at")
    private LocalDateTime processedAt;

    @Column(name = "anomaly_detection_id")
    private Long anomalyDetectionId;

    @Column(name = "ml_service_version")
    private String mlServiceVersion;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "created_by")
    private String createdBy;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Column(name = "updated_by")
    private String updatedBy;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    @Column(name = "deleted_by")
    private String deletedBy;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "metadata", columnDefinition = "jsonb")
    private Map<String, Object> metadata;

    @PrePersist
    protected void onCreate() {
        if (createdAt == null)
            createdAt = LocalDateTime.now();
        if (updatedAt == null)
            updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
