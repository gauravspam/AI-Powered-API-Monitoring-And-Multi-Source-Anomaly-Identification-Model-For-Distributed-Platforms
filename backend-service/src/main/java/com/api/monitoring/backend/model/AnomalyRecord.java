package com.api.monitoring.backend.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.Map;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

/**
 * AnomalyRecord Entity: Represents ML anomaly detection results
 * Table: anomaly_detections
 */
@Entity
@Table(name = "anomaly_detections", indexes = {
        @Index(name = "idx_anomaly_detections_endpoint", columnList = "endpoint"),
        @Index(name = "idx_anomaly_detections_severity", columnList = "severity_level"),
        @Index(name = "idx_anomaly_detections_status", columnList = "status"),
        @Index(name = "idx_anomaly_detections_created_at", columnList = "created_at DESC"),
        @Index(name = "idx_anomaly_detections_trace_id", columnList = "trace_id"),
        @Index(name = "idx_anomaly_detections_api_log_id", columnList = "api_log_id"),
        @Index(name = "idx_anomaly_detections_severity_status", columnList = "severity_level, status, created_at DESC")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@EqualsAndHashCode(of = "id")
@ToString(exclude = "additionalContext")
public class AnomalyRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "anomaly_detections_id_seq")
    @SequenceGenerator(name = "anomaly_detections_id_seq", sequenceName = "anomaly_detections_id_seq", allocationSize = 1)
    private Long id;

    @Column(name = "api_log_id")
    private Long apiLogId;

    @Column(name = "endpoint", nullable = false, length = 500)
    private String endpoint;

    @Column(name = "http_method", nullable = false, length = 10)
    private String method;

    @Column(name = "msif_lstm_score", nullable = false)
    private Double msifLstmScore;

    @Column(name = "ple_gru_score", nullable = false)
    private Double pleGruScore;

    @Column(name = "hybrid_ensemble_score", nullable = false)
    private Double hybridEnsembleScore;

    @Column(name = "confidence_score", nullable = false)
    private Double confidence;

    @Column(name = "severity_level", nullable = false, length = 50)
    private String severity;

    @Column(name = "anomaly_type", length = 100)
    private String anomalyType;

    @Column(name = "fusion_method", nullable = false, length = 100)
    private String fusionMethod;

    @Column(name = "ml_model_version", length = 50)
    private String mlServiceVersion;

    @Column(name = "ml_processing_time_ms")
    private Long mlProcessingTimeMs;

    @Column(name = "status", nullable = false, length = 50)
    @Builder.Default
    private String status = "ACTIVE";

    @Column(name = "is_acknowledged")
    @Builder.Default
    private Boolean isAcknowledged = false;

    @Column(name = "acknowledged_by", length = 255)
    private String acknowledgedBy;

    @Column(name = "acknowledged_at")
    private LocalDateTime acknowledgedAt;

    @Column(name = "acknowledgement_note", columnDefinition = "TEXT")
    private String acknowledgementNote;

    @Column(name = "is_resolved")
    @Builder.Default
    private Boolean isResolved = false;

    @Column(name = "resolved_by", length = 255)
    private String resolvedBy;

    @Column(name = "resolved_at")
    private LocalDateTime resolvedAt;

    @Column(name = "resolution_note", columnDefinition = "TEXT")
    private String resolutionNote;

    @Column(name = "is_false_positive")
    @Builder.Default
    private Boolean isFalsePositive = false;

    @Column(name = "marked_false_positive_by", length = 255)
    private String markedFalsePositiveBy;

    @Column(name = "marked_false_positive_at")
    private LocalDateTime markedFalsePositiveAt;

    @Column(name = "trace_id", length = 255)
    private String traceId;

    @Column(name = "service_name", length = 255)
    private String serviceName;

    @Column(name = "environment", length = 50)
    private String environment;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "created_by", length = 255)
    private String createdBy;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Column(name = "updated_by", length = 255)
    private String updatedBy;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    @Column(name = "deleted_by", length = 255)
    private String deletedBy;

    // ✅ FIXED: Use Hibernate 6 native JSONB support
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "additional_context", columnDefinition = "jsonb")
    private Map<String, Object> additionalContext;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }

    public void acknowledge(String username) {
        this.isAcknowledged = true;
        this.acknowledgedBy = username;
        this.acknowledgedAt = LocalDateTime.now();
    }

    public void resolve() {
        this.isResolved = true;
        this.resolvedBy = "SYSTEM";
        this.resolvedAt = LocalDateTime.now();
        this.status = "RESOLVED";
    }

    public void markAsFalsePositive(String username) {
        this.isFalsePositive = true;
        this.markedFalsePositiveBy = username;
        this.markedFalsePositiveAt = LocalDateTime.now();
        this.status = "FALSE_POSITIVE";
    }

    public void delete(String deletedBy) {
        this.deletedAt = LocalDateTime.now();
        this.deletedBy = deletedBy;
    }

    public boolean isDeleted() {
        return deletedAt != null;
    }

    public boolean isCriticalUnacknowledged() {
        return !isAcknowledged && ("CRITICAL".equals(severity) || "HIGH".equals(severity));
    }

    public Double getAnomalyScore() {
        return hybridEnsembleScore;
    }
}
