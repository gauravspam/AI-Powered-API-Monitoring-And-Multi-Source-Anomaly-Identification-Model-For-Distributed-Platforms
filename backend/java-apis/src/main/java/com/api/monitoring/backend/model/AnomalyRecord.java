package com.api.monitoring.backend.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "anomalies")
public class AnomalyRecord {
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private UUID id;

    @Column(name = "api_name", nullable = false)
    private String apiName;

    @Column(nullable = false)
    private LocalDateTime timestamp;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Severity severity;

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

    // Constructors
    public AnomalyRecord() {
    }

    public AnomalyRecord(String apiName, LocalDateTime timestamp, Severity severity, Double confidenceScore, String metricValues, String mlModelUsed) {
        this.apiName = apiName;
        this.timestamp = timestamp;
        this.severity = severity;
        this.confidenceScore = confidenceScore;
        this.metricValues = metricValues;
        this.mlModelUsed = mlModelUsed;
        this.createdAt = LocalDateTime.now();
    }

    // Getters and Setters
    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
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

    public Severity getSeverity() {
        return severity;
    }

    public void setSeverity(Severity severity) {
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

    // Enum for Severity
    public enum Severity {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }
}
