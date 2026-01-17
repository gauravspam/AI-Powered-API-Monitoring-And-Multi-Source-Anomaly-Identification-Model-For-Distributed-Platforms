package com.api.monitoring.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class StatisticsResponse {
    @JsonProperty("api_name")
    private String apiName;
    
    @JsonProperty("total_logs")
    private Long totalLogs;
    
    @JsonProperty("normal_count")
    private Long normalCount;
    
    @JsonProperty("suspicious_count")
    private Long suspiciousCount;
    
    @JsonProperty("anomaly_count")
    private Long anomalyCount;
    
    @JsonProperty("avg_anomaly_score")
    private Double avgAnomalyScore;
    
    @JsonProperty("peak_hour")
    private Integer peakHour;
    
    @JsonProperty("last_24h_anomalies")
    private Long last24hAnomalies;
    
    @JsonProperty("alerts_triggered")
    private Long alertsTriggered;
    
    @JsonProperty("error_rate_trend")
    private String errorRateTrend;

    // Constructors
    public StatisticsResponse() {}

    // Getters and Setters
    public String getApiName() {
        return apiName;
    }

    public void setApiName(String apiName) {
        this.apiName = apiName;
    }

    public Long getTotalLogs() {
        return totalLogs;
    }

    public void setTotalLogs(Long totalLogs) {
        this.totalLogs = totalLogs;
    }

    public Long getNormalCount() {
        return normalCount;
    }

    public void setNormalCount(Long normalCount) {
        this.normalCount = normalCount;
    }

    public Long getSuspiciousCount() {
        return suspiciousCount;
    }

    public void setSuspiciousCount(Long suspiciousCount) {
        this.suspiciousCount = suspiciousCount;
    }

    public Long getAnomalyCount() {
        return anomalyCount;
    }

    public void setAnomalyCount(Long anomalyCount) {
        this.anomalyCount = anomalyCount;
    }

    public Double getAvgAnomalyScore() {
        return avgAnomalyScore;
    }

    public void setAvgAnomalyScore(Double avgAnomalyScore) {
        this.avgAnomalyScore = avgAnomalyScore;
    }

    public Integer getPeakHour() {
        return peakHour;
    }

    public void setPeakHour(Integer peakHour) {
        this.peakHour = peakHour;
    }

    public Long getLast24hAnomalies() {
        return last24hAnomalies;
    }

    public void setLast24hAnomalies(Long last24hAnomalies) {
        this.last24hAnomalies = last24hAnomalies;
    }

    public Long getAlertsTriggered() {
        return alertsTriggered;
    }

    public void setAlertsTriggered(Long alertsTriggered) {
        this.alertsTriggered = alertsTriggered;
    }

    public String getErrorRateTrend() {
        return errorRateTrend;
    }

    public void setErrorRateTrend(String errorRateTrend) {
        this.errorRateTrend = errorRateTrend;
    }
}

