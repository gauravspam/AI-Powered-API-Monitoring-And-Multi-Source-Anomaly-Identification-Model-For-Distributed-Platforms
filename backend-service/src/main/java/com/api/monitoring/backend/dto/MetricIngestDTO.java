package com.api.monitoring.backend.dto;

import java.time.Instant;
import java.time.LocalDateTime;

public class MetricIngestDTO {
    private Long apiId;
    private Double cpuUsage;
    private Double memoryUsage;
    private Double responseTimeMs;
    private Double errorRate;
    private Integer requestCount;
    private LocalDateTime timestamp;

    // Constructors
    public MetricIngestDTO() {}

    public MetricIngestDTO(Long apiId, Double responseTimeMs, Integer requestCount) {
        this.apiId = apiId;
        this.responseTimeMs = responseTimeMs;
        this.requestCount = requestCount;
        this.timestamp = LocalDateTime.now();
    }

    // Getters and Setters
    public Long getApiId() { return apiId; }
    public void setApiId(Long apiId) { this.apiId = apiId; }
    
    public Double getCpuUsage() { return cpuUsage; }
    public void setCpuUsage(Double cpuUsage) { this.cpuUsage = cpuUsage; }
    
    public Double getMemoryUsage() { return memoryUsage; }
    public void setMemoryUsage(Double memoryUsage) { this.memoryUsage = memoryUsage; }
    
    public Double getResponseTimeMs() { return responseTimeMs; }
    public void setResponseTimeMs(Double responseTimeMs) { this.responseTimeMs = responseTimeMs; }
    
    public Double getErrorRate() { return errorRate; }
    public void setErrorRate(Double errorRate) { this.errorRate = errorRate; }
    
    public Integer getRequestCount() { return requestCount; }
    public void setRequestCount(Integer requestCount) { this.requestCount = requestCount; }
    
    public LocalDateTime getTimestamp() { return timestamp; }
    public void setTimestamp(LocalDateTime timestamp) { this.timestamp = timestamp; }
}
