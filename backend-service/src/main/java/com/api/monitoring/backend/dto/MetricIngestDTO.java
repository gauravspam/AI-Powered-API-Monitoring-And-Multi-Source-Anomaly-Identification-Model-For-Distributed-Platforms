package com.api.monitoring.backend.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class MetricIngestDTO {
    private Long apiId;
    private String serviceName; // ADD THIS
    private Double cpuUsage;
    private Double memoryUsage;
    private Long diskIoBytes;
    private Long networkIoBytes;
    private Double responseTimeMs;
    private Integer requestCount;
    private Double errorRate;
    private LocalDateTime timestamp;

    public MetricIngestDTO(Long apiId, Double responseTimeMs, Integer requestCount) {
        this.apiId = apiId;
        this.responseTimeMs = responseTimeMs;
        this.requestCount = requestCount;
        this.timestamp = LocalDateTime.now();
    }

    // Getters and Setters
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
