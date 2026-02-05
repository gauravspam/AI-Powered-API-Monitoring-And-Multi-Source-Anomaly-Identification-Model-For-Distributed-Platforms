package com.api.monitoring.backend.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import java.time.LocalDateTime;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "distributedtraces", indexes = {
        @Index(name = "idxtraceid", columnList = "traceid"),
        @Index(name = "idxservicename", columnList = "servicename"),
        @Index(name = "idxtimestamp", columnList = "timestamp")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TraceRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "traceid", nullable = false, length = 100)
    private String traceId;

    @Column(name = "spanid", length = 100)
    private String spanId;

    @Column(name = "parentspanid", length = 100)
    private String parentSpanId;

    @Column(name = "servicename", nullable = false)
    private String serviceName;

    @Column(name = "operationname")
    private String operationName;

    /**
     * Keep the Java field name as "duration" because TraceRepository uses it in
     * JPQL: AVG(t.duration).
     */
    @Column(name = "durationms")
    private Long duration;

    @Column(name = "statuscode")
    private Integer statusCode;

    /**
     * Keep the Java field name as "timestamp" because controllers sort by
     * "timestamp" property.
     */
    @Column(name = "timestamp", nullable = false)
    private LocalDateTime timestamp;

    /**
     * Stored as JSON string currently because TracesController writes/reads it as
     * String.
     */
    @Column(name = "tags", columnDefinition = "TEXT")
    private String tags;

    @Column(name = "createdat", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        LocalDateTime now = LocalDateTime.now();
        if (createdAt == null)
            createdAt = now;
        if (timestamp == null)
            timestamp = now;
    }
}
