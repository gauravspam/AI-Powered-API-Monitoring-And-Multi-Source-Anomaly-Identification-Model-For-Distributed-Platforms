package com.api.monitoring.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class MetricIngestDTO {
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
    
    // Alias setters for snake_case from JSON
    public void setService_name(String val) { this.serviceName = val; }
    public void setCpu_usage(Double val) { this.cpuUsage = val; }
    public void setMemory_usage(Double val) { this.memoryUsage = val; }
    public void setDisk_io_bytes(Long val) { this.diskIoBytes = val; }
    public void setNetwork_io_bytes(Long val) { this.networkIoBytes = val; }
    public void setResponse_time_ms(Double val) { this.responseTimeMs = val; }
    public void setRequest_count(Integer val) { this.requestCount = val; }
    public void setError_rate(Double val) { this.errorRate = val; }
}