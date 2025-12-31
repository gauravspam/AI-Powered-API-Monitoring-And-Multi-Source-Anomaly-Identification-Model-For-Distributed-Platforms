package com.api.monitoring.backend.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "anomalies")
public class AnomalyRecord {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "api_name", nullable = false)
    private String apiName;

    @Column(nullable = false)
    private LocalDateTime timestamp;

    // Add more fields as needed, e.g., description, severity, etc.
    @Column
    private String severity;

    @Column(name = "confidence_score", precision = 5, scale = 2)
    private Double confidenceScore;

    @Column(name = "metric_values", columnDefinition = "jsonb")
    private String metricValues;

    @Column(name = "ml_model_used")
    private String mlModelUsed;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    // Additional fields for anomaly detection
    @Column
    private Integer stage;

    @Column
    private String model;

    @Column(name = "anomaly_score")
    private Double anomalyScore;

    @Column(name = "stage2_score")
    private Double stage2Score;

    @Column(name = "final_anomaly_score")
    private Double finalAnomalyScore;

    @Column
    private String status;

    @Column
    private Double confidence;

    @Column
    private Boolean acknowledged = false;

    // Constructors
    public AnomalyRecord() {
    }

    public AnomalyRecord(String apiName, LocalDateTime timestamp, String severity, Double confidenceScore, String metricValues, String mlModelUsed) {
        this.apiName = apiName;
        this.timestamp = timestamp;
        this.severity = severity;
        this.confidenceScore = confidenceScore;
        this.metricValues = metricValues;
        this.mlModelUsed = mlModelUsed;
        this.createdAt = LocalDateTime.now();
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

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }

    public String getSeverity() {
        return severity;
    }

    public void setSeverity(String severity) {
        this.severity = severity;
    }

    public Double getConfidenceScore() {
        return confidenceScore;
    }

    public void setConfidenceScore(Double confidenceScore) {
        this.confidenceScore = confidenceScore;
    }

    public String getMetricValues() {
        return metricValues;
    }

    public void setMetricValues(String metricValues) {
        this.metricValues = metricValues;
    }

    public String getMlModelUsed() {
        return mlModelUsed;
    }

    public void setMlModelUsed(String mlModelUsed) {
        this.mlModelUsed = mlModelUsed;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
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

    public Double getConfidence() {
        return confidence;
    }

    public void setConfidence(Double confidence) {
        this.confidence = confidence;
    }

    public Boolean getAcknowledged() {
        return acknowledged;
    }

    public void setAcknowledged(Boolean acknowledged) {
        this.acknowledged = acknowledged;
    }
}
