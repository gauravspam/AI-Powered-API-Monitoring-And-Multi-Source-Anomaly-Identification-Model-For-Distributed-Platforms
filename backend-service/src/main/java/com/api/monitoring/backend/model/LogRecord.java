package com.api.monitoring.backend.model;

import jakarta.persistence.*;
import java.time.Duration;
import java.time.LocalDateTime;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

/**
 * Entity representing API log entries
 * Maps to api_logs table
 * Stores all API request/response data for monitoring and analysis
 */
@Entity
@Table(
    name = "api_logs",
    indexes = {
        @Index(name = "idx_api_logs_endpoint", columnList = "endpoint"),
        @Index(name = "idx_api_logs_status_code", columnList = "status_code"),
        @Index(name = "idx_api_logs_created_at", columnList = "created_at"),
        @Index(
            name = "idx_api_logs_processed_created_at",
            columnList = "processed, created_at"
        ),
    }
)
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class LogRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // API Request Details
    @Column(name = "endpoint", nullable = false, length = 500)
    private String endpoint;

    @Column(name = "method", nullable = false, length = 10)
    @Builder.Default
    private String method = "GET";

    @Column(name = "status_code")
    private Integer statusCode;

    // Performance Metrics
    @Column(name = "response_time_ms")
    private Long responseTimeMs;

    @Column(name = "request_size")
    private Long requestSize;

    @Column(name = "response_size")
    private Long responseSize;

    // System Metrics
    @Column(name = "cpu_usage")
    private Double cpuUsage;

    @Column(name = "memory_usage")
    private Double memoryUsage;

    @Column(name = "error_rate")
    private Double errorRate;

    @Column(name = "request_count")
    @Builder.Default
    private Integer requestCount = 1;

    // Network Metrics
    @Column(name = "network_io")
    private Long networkIo;

    @Column(name = "disk_io")
    private Long diskIo;

    // Request Context
    @Column(name = "trace_id", length = 255)
    private String traceId;

    @Column(name = "environment", length = 50)
    private String environment;

    @Column(name = "service_name", length = 255)
    private String serviceName;

    @Column(name = "user_id", length = 255)
    private String userId;

    @Column(name = "ip_address", length = 45)
    private String ipAddress;

    // Request/Response Bodies (optional)
    @Column(name = "request_body", columnDefinition = "TEXT")
    private String requestBody;

    @Column(name = "response_body", columnDefinition = "TEXT")
    private String responseBody;

    @Column(name = "error_message", columnDefinition = "TEXT")
    private String errorMessage;

    @Column(name = "stack_trace", columnDefinition = "TEXT")
    private String stackTrace;

    // ============= ML PROCESSING FIELDS (Priority 1) =============

    /**
     * Whether this log has been processed by ML service
     */
    @Column(name = "processed", nullable = false)
    @Builder.Default
    private Boolean processed = false;

    /**
     * Timestamp when ML analysis completed
     */
    @Column(name = "processed_at")
    private LocalDateTime processedAt;

    /**
     * Foreign key to anomaly_scores table if anomaly was detected
     */
    @Column(name = "anomaly_id")
    private Long anomalyId;

    /**
     * Version of ML service that processed this log
     */
    @Column(name = "ml_service_version", length = 50)
    private String mlServiceVersion;

    // ============= END ML PROCESSING FIELDS =============

    // Temporal Data
    @Column(name = "hour_of_day")
    private Integer hourOfDay;

    @Column(name = "day_of_week")
    private Integer dayOfWeek;

    // Audit Timestamps
    @Column(name = "timestamp")
    private LocalDateTime timestamp;

    @Column(name = "created_at", nullable = false, updatable = false)
    @CreationTimestamp
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    @UpdateTimestamp
    private LocalDateTime updatedAt;

    // ============= HELPER METHODS =============

    /**
     * Check if log has been processed
     */
    @Transient
    public boolean isProcessed() {
        return Boolean.TRUE.equals(processed);
    }

    /**
     * Check if anomaly was detected for this log
     */
    @Transient
    public boolean hasAnomaly() {
        return anomalyId != null;
    }

    /**
     * Calculate processing duration
     */
    @Transient
    public Duration getProcessingDuration() {
        if (createdAt != null && processedAt != null) {
            return Duration.between(createdAt, processedAt);
        }
        return null;
    }

    /**
     * Mark this log as processed
     */
    public void markAsProcessed(Long anomalyId, String mlVersion) {
        this.processed = true;
        this.processedAt = LocalDateTime.now();
        this.anomalyId = anomalyId;
        this.mlServiceVersion = mlVersion;
    }

    /**
     * Check if this log needs processing
     */
    @Transient
    public boolean needsProcessing() {
        return !Boolean.TRUE.equals(processed);
    }

    /**
     * Check if this is an error response
     */
    @Transient
    public boolean isError() {
        return statusCode != null && statusCode >= 400;
    }

    /**
     * Check if this is a slow response
     */
    @Transient
    public boolean isSlowResponse(long thresholdMs) {
        return responseTimeMs != null && responseTimeMs > thresholdMs;
    }

    /**
     * Calculate error rate (0.0 to 1.0)
     */
    @Transient
    public Double calculateErrorRate() {
        if (errorRate != null) {
            return errorRate;
        }
        return isError() ? 1.0 : 0.0;
    }

    /**
     * Get response time in seconds
     */
    @Transient
    public Double getResponseTimeSeconds() {
        return responseTimeMs != null ? responseTimeMs / 1000.0 : null;
    }

    /**
     * Extract hour and day from timestamp
     */
    @PrePersist
    @PreUpdate
    public void extractTemporalFeatures() {
        LocalDateTime time =
            timestamp != null ? timestamp : LocalDateTime.now();
        this.hourOfDay = time.getHour();
        this.dayOfWeek = time.getDayOfWeek().getValue();
    }

    /**
     * Validate data before persistence
     */
    @PrePersist
    public void prePersist() {
        if (this.timestamp == null) {
            this.timestamp = LocalDateTime.now();
        }
        if (this.processed == null) {
            this.processed = false;
        }
        extractTemporalFeatures();
    }
}
