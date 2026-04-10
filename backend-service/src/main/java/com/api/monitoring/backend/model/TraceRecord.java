package com.api.monitoring.backend.model;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.Map;

@Entity
@Table(name = "distributed_traces")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TraceRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "trace_id", nullable = false)
    private String traceId;

    @Column(name = "span_id", nullable = false)
    private String spanId;

    @Column(name = "parent_span_id")
    private String parentSpanId;

    @Column(name = "service_name", nullable = false)
    private String serviceName;

    @Column(name = "operation_name")
    private String operationName;

    @Column(name = "start_time", nullable = false)
    private LocalDateTime startTime;

    @Column(name = "duration_ms", nullable = false)
    private Long duration;

    @Column(name = "status_code")
    private Integer statusCode;

    @Column(name = "is_error")
    private Boolean isError;

    @Column(name = "error_message", columnDefinition = "TEXT")
    private String errorMessage;

    @Column(name = "tags", columnDefinition = "JSONB")
    @org.hibernate.annotations.JdbcTypeCode(org.hibernate.type.SqlTypes.JSON)
    private Map<String, Object> tags;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;
}
