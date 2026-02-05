package com.api.monitoring.backend.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import java.time.LocalDateTime;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "systemmetrics")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class MetricRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * NOTE: your repositories/controllers use "apiId" and query methods like
     * findByApiIdAndTimestampAfter(...).
     * Keep the Java field name as apiId even if you later change the DB column
     * during the migration cleanup.
     */
    @Column(name = "apiid", nullable = false)
    private Long apiId;

    @Column(name = "cpuusage")
    private Double cpuUsage;

    @Column(name = "memoryusage")
    private Double memoryUsage;

    @Column(name = "responsetimems")
    private Double responseTimeMs;

    @Column(name = "errorrate")
    private Double errorRate;

    @Column(name = "requestcount")
    private Integer requestCount;

    @Column(name = "timestamp", nullable = false)
    private LocalDateTime timestamp;

    @Column(name = "createdat")
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        if (createdAt == null)
            createdAt = LocalDateTime.now();
        if (timestamp == null)
            timestamp = LocalDateTime.now();
    }
}
