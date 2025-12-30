package com.api.monitoring.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.LocalDateTime;

public class AnomalyResponse {
    private String apiName;
    private Integer stage;
    private String model;
    private Double anomalyScore;
    private Double stage2Score;
    private Double finalAnomalyScore;
    private String status;
    private String severity;
    private Double confidence;
    private String timestamp;
    private Long id; // For acknowledge endpoint

    // Constructors
    public AnomalyResponse() {}

    // Getters and Setters
    @JsonProperty("api_name")
    public String getApiName() {
        return apiName;
    }

    @JsonProperty("api_name")
    public void setApiName(String apiName) {
        this.apiName = apiName;
    }

    public Integer getStage() {
        return stage;
    }

    public void setStage(Integer stage) {
        this.stage = stage;
    }

    public String getModel() {
        return model;
    }

    public void setModel(String model) {
        this.model = model;
    }

    @JsonProperty("anomaly_score")
    public Double getAnomalyScore() {
        return anomalyScore;
    }

    @JsonProperty("anomaly_score")
    public void setAnomalyScore(Double anomalyScore) {
        this.anomalyScore = anomalyScore;
    }

    @JsonProperty("stage2_score")
    public Double getStage2Score() {
        return stage2Score;
    }

    @JsonProperty("stage2_score")
    public void setStage2Score(Double stage2Score) {
        this.stage2Score = stage2Score;
    }

    @JsonProperty("final_anomaly_score")
    public Double getFinalAnomalyScore() {
        return finalAnomalyScore;
    }

    @JsonProperty("final_anomaly_score")
    public void setFinalAnomalyScore(Double finalAnomalyScore) {
        this.finalAnomalyScore = finalAnomalyScore;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getSeverity() {
        return severity;
    }

    public void setSeverity(String severity) {
        this.severity = severity;
    }

    public Double getConfidence() {
        return confidence;
    }

    public void setConfidence(Double confidence) {
        this.confidence = confidence;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }
}

