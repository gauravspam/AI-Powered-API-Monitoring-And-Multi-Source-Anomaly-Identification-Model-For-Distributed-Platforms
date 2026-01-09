package com.api.monitoring.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * Entity to store anomaly detection results
 */
@Entity
@Table(name = "anomaly_scores", indexes = {
    @Index(name = "idx_api_timestamp", columnList = "api_endpoint, timestamp"),
    @Index(name = "idx_severity", columnList = "severity"),
    @Index(name = "idx_timestamp", columnList = "timestamp")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
public class AnomalyScore {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "api_endpoint", nullable = false, length = 255)
    private String apiEndpoint;
    
    @Column(name = "method", nullable = false, length = 10)
    private String method;
    
    @Column(name = "anomaly_type", nullable = false, length = 50)
    private String anomalyType;
    
    @Column(name = "score", nullable = false)
    private Float score;
    
    @Column(name = "severity", length = 20)
    private String severity;
    
    @Column(name = "timestamp")
    private LocalDateTime timestamp;
    
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        if (timestamp == null) {
            timestamp = LocalDateTime.now();
        }
        if (score != null) {
            severity = determineSeverity(score);
        }
    }
    
    private String determineSeverity(Float score) {
        if (score == null) {
            return "UNKNOWN";
        }
        if (score > 0.8) {
            return "CRITICAL";
        } else if (score > 0.6) {
            return "HIGH";
        } else if (score > 0.4) {
            return "MEDIUM";
        } else {
            return "LOW";
        }
    }
}