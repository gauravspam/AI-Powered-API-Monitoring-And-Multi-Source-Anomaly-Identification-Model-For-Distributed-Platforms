package com.api.monitoring.backend.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "metrics")
public class MetricRecord {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "api_id", nullable = false)
    private Long apiId;

    @Column()

    private Double cpuUsage;

    @Column()

    private Double memoryUsage;

    @Column()

    private Double responseTimeMs;

    @Column()

    private Double errorRate;

    @Column(name = "request_count")
    private Integer requestCount;

    @Column(nullable = false)
    private LocalDateTime timestamp;

    // Constructors
    public MetricRecord() {
    }

    public MetricRecord(Long apiId, Double cpuUsage, Double memoryUsage, Double responseTimeMs, Double errorRate,
            Integer requestCount, LocalDateTime timestamp) {
        this.apiId = apiId;
        this.cpuUsage = cpuUsage;
        this.memoryUsage = memoryUsage;
        this.responseTimeMs = responseTimeMs;
        this.errorRate = errorRate;
        this.requestCount = requestCount;
        this.timestamp = timestamp;
    }

    // Getters and Setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getApiId() {
        return apiId;
    }

    public void setApiId(Long apiId) {
        this.apiId = apiId;
    }

    public Double getCpuUsage() {
        return cpuUsage;
    }

    public void setCpuUsage(Double cpuUsage) {
        this.cpuUsage = cpuUsage;
    }

    public Double getMemoryUsage() {
        return memoryUsage;
    }

    public void setMemoryUsage(Double memoryUsage) {
        this.memoryUsage = memoryUsage;
    }

    public Double getResponseTimeMs() {
        return responseTimeMs;
    }

    public void setResponseTimeMs(Double responseTimeMs) {
        this.responseTimeMs = responseTimeMs;
    }

    public Double getErrorRate() {
        return errorRate;
    }

    public void setErrorRate(Double errorRate) {
        this.errorRate = errorRate;
    }

    public Integer getRequestCount() {
        return requestCount;
    }

    public void setRequestCount(Integer requestCount) {
        this.requestCount = requestCount;
    }

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }
}