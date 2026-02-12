package com.api.monitoring.backend.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.Map;
import com.fasterxml.jackson.annotation.JsonProperty;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Table(name = "anomaly_detections", indexes = {
        @Index(name = "idx_anomaly_detections_endpoint", columnList = "endpoint"),
        @Index(name = "idx_anomaly_detections_severity", columnList = "severity_level"),
        @Index(name = "idx_anomaly_detections_status", columnList = "status"),
        @Index(name = "idx_anomaly_detections_created_at", columnList = "created_at DESC")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AnomalyRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
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

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "additional_context", columnDefinition = "jsonb")
    private Map<String, Object> additionalContext;

    public void setAcknowledged(boolean acknowledged) {
        this.isAcknowledged = acknowledged;
    }
}
