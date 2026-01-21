package com.api.monitoring.backend.model;

import java.time.LocalDateTime;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

/**
 * Entity representing ML anomaly detection results
 * Maps to anomaly_scores table
 * Stores predictions from hybrid MSIF-LSTM + PLE-GRU models
 */
@Entity
@Table(name = "anomaly_scores")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AnomalyRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // API Identification
    @Column(name = "endpoint", nullable = false)
    private String endpoint;

    @Column(name = "method", nullable = false)
    private String method;

    // ML Model Scores
    @Column(name = "msif_lstm_score")
    private Double msifLstmScore;

    @Column(name = "ple_gru_score")
    private Double pleGruScore;

    @Column(name = "hybrid_ensemble_score", nullable = false)
    private Double hybridEnsembleScore;

    // Analysis Metadata
    @Column(name = "confidence")
    private Double confidence;

    @Column(name = "severity", nullable = false)
    private String severity;

    @Column(name = "fusion_method")
    private String fusionMethod;

    // Status Tracking
    @Column(name = "status", nullable = false)
    @Builder.Default
    private String status = "ACTIVE";

    @Column(name = "acknowledged")
    @Builder.Default
    private Boolean acknowledged = false;

    @Column(name = "acknowledged_by")
    private String acknowledgedBy;

    @Column(name = "acknowledged_at")
    private LocalDateTime acknowledgedAt;

    // Diagnostics & Tracing
    @Column(name = "trace_id")
    private String traceId;

    @Column(name = "ml_processing_time_ms")
    private Long mlProcessingTimeMs;

    @Column(name = "ml_service_version")
    private String mlServiceVersion;

    // Audit Timestamps
    @Column(name = "created_at", nullable = false, updatable = false)
    @CreationTimestamp
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    @UpdateTimestamp
    private LocalDateTime updatedAt;

    // Helper methods for severity classification
    @Transient
    public boolean isCritical() {
        return "CRITICAL".equalsIgnoreCase(severity);
    }

    @Transient
    public boolean isHigh() {
        return "HIGH".equalsIgnoreCase(severity);
    }

    @Transient
    public boolean isActive() {
        return "ACTIVE".equalsIgnoreCase(status);
    }

    @Transient
    public boolean isAcknowledged() {
        return Boolean.TRUE.equals(acknowledged);
    }

    /**
     * Calculate severity from hybrid score
     * @param score Hybrid ensemble score (0.0 - 1.0)
     * @return Severity level
     */
    public static String calculateSeverity(Double score) {
        if (score == null) return "UNKNOWN";
        if (score >= 0.8) return "CRITICAL";
        if (score >= 0.6) return "HIGH";
        if (score >= 0.4) return "MEDIUM";  
        return "LOW";
    }

    /**
     * Mark this anomaly as acknowledged
     */
    public void acknowledge(String username) {
        this.acknowledged = true;
        this.acknowledgedBy = username;
        this.acknowledgedAt = LocalDateTime.now();
        this.status = "ACKNOWLEDGED";
    }

    /**
     * Mark this anomaly as resolved
     */
    public void resolve() {
        this.status = "RESOLVED";
    }
}
