package com.api.monitoring.backend.model;

import java.time.LocalDateTime;
import java.util.concurrent.atomic.AtomicLong;

public class AnomalyRecord {
    private static final AtomicLong idGenerator = new AtomicLong(1);
    
    private Long id;
    private String apiName;
    private Integer stage;
    private String model;
    private Double anomalyScore;
    private Double stage2Score;
    private Double finalAnomalyScore;
    private String status;
    private String severity;
    private Double confidence;
    private LocalDateTime timestamp;
    private Boolean acknowledged;

    public AnomalyRecord() {
        this.id = idGenerator.getAndIncrement();
        this.timestamp = LocalDateTime.now();
        this.acknowledged = false;
    }

    // Getters and Setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getApiName() {
        return apiName;
    }

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

    public Double getAnomalyScore() {
        return anomalyScore;
    }

    public void setAnomalyScore(Double anomalyScore) {
        this.anomalyScore = anomalyScore;
    }

    public Double getStage2Score() {
        return stage2Score;
    }

    public void setStage2Score(Double stage2Score) {
        this.stage2Score = stage2Score;
    }

    public Double getFinalAnomalyScore() {
        return finalAnomalyScore;
    }

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

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }

    public Boolean getAcknowledged() {
        return acknowledged;
    }

    public void setAcknowledged(Boolean acknowledged) {
        this.acknowledged = acknowledged;
    }
}

