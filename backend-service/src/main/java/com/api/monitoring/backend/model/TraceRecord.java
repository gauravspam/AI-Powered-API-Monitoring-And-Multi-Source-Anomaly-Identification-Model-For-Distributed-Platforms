package com.api.monitoring.backend.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.Map;

@Entity
@Table(name = "traces", indexes = {
    @Index(name = "idx_trace_id", columnList = "trace_id"),
    @Index(name = "idx_service_name", columnList = "service_name"),
    @Index(name = "idx_timestamp", columnList = "timestamp")
})
public class TraceRecord {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "trace_id", nullable = false, length = 100)
    private String traceId;

    @Column(name = "span_id", length = 100)
    private String spanId;

    @Column(name = "parent_span_id", length = 100)
    private String parentSpanId;

    @Column(name = "service_name", nullable = false)
    private String serviceName;

    @Column(name = "operation_name")
    private String operationName;

    @Column(name = "duration_ms")
    private Long duration;

    @Column(name = "status_code")
    private Integer statusCode;

    @Column(nullable = false)
    private LocalDateTime timestamp;

    @Column(name = "tags", columnDefinition = "TEXT")
    private String tags; // JSON string

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        if (timestamp == null) {
            timestamp = LocalDateTime.now();
        }
    }

    // Constructors
    public TraceRecord() {}

    public TraceRecord(String traceId, String serviceName, String operationName, Long duration) {
        this.traceId = traceId;
        this.serviceName = serviceName;
        this.operationName = operationName;
        this.duration = duration;
        this.timestamp = LocalDateTime.now();
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getTraceId() { return traceId; }
    public void setTraceId(String traceId) { this.traceId = traceId; }

    public String getSpanId() { return spanId; }
    public void setSpanId(String spanId) { this.spanId = spanId; }

    public String getParentSpanId() { return parentSpanId; }
    public void setParentSpanId(String parentSpanId) { this.parentSpanId = parentSpanId; }

    public String getServiceName() { return serviceName; }
    public void setServiceName(String serviceName) { this.serviceName = serviceName; }

    public String getOperationName() { return operationName; }
    public void setOperationName(String operationName) { this.operationName = operationName; }

    public Long getDuration() { return duration; }
    public void setDuration(Long duration) { this.duration = duration; }

    public Integer getStatusCode() { return statusCode; }
    public void setStatusCode(Integer statusCode) { this.statusCode = statusCode; }

    public LocalDateTime getTimestamp() { return timestamp; }
    public void setTimestamp(LocalDateTime timestamp) { this.timestamp = timestamp; }

    public String getTags() { return tags; }
    public void setTags(String tags) { this.tags = tags; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
