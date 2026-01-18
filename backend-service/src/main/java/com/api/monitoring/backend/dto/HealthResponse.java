package com.api.monitoring.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class HealthResponse {
    private String status;
    
    @JsonProperty("pythonServiceStatus")
    private Boolean pythonServiceStatus;
    
    @JsonProperty("databaseStatus")
    private Boolean databaseStatus;
    
    @JsonProperty("totalApisMonitored")
    private Integer totalApisMonitored;
    
    @JsonProperty("activeAlerts")
    private Integer activeAlerts;
    
    @JsonProperty("processingLatencyMs")
    private Long processingLatencyMs;
    
    @JsonProperty("uptimePercentage")
    private Double uptimePercentage;

    // Constructors
    public HealthResponse() {}

    // Getters and Setters
    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public Boolean getPythonServiceStatus() {
        return pythonServiceStatus;
    }

    public void setPythonServiceStatus(Boolean pythonServiceStatus) {
        this.pythonServiceStatus = pythonServiceStatus;
    }

    public Boolean getDatabaseStatus() {
        return databaseStatus;
    }

    public void setDatabaseStatus(Boolean databaseStatus) {
        this.databaseStatus = databaseStatus;
    }

    public Integer getTotalApisMonitored() {
        return totalApisMonitored;
    }

    public void setTotalApisMonitored(Integer totalApisMonitored) {
        this.totalApisMonitored = totalApisMonitored;
    }

    public Integer getActiveAlerts() {
        return activeAlerts;
    }

    public void setActiveAlerts(Integer activeAlerts) {
        this.activeAlerts = activeAlerts;
    }

    public Long getProcessingLatencyMs() {
        return processingLatencyMs;
    }

    public void setProcessingLatencyMs(Long processingLatencyMs) {
        this.processingLatencyMs = processingLatencyMs;
    }

    public Double getUptimePercentage() {
        return uptimePercentage;
    }

    public void setUptimePercentage(Double uptimePercentage) {
        this.uptimePercentage = uptimePercentage;
    }
}

