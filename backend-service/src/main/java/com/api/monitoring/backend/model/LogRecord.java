package com.api.monitoring.backend.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.SequenceGenerator;
import jakarta.persistence.Table;
import java.time.LocalDateTime;
import java.util.Map;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;
import lombok.ToString;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Table(name = "apilogs", indexes = {
        @Index(name = "idxapilogsendpoint", columnList = "endpoint"),
        @Index(name = "idxapilogsstatuscode", columnList = "statuscode"),
        @Index(name = "idxapilogscreatedat", columnList = "createdat DESC"),
        @Index(name = "idxapilogstraceid", columnList = "traceid"),
        @Index(name = "idxapilogsendpointcreated", columnList = "endpoint, createdat DESC"),
        @Index(name = "idxapilogsservicecreated", columnList = "servicename, createdat DESC"),
        @Index(name = "idxapilogsunprocessed", columnList = "isprocessed, createdat")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@EqualsAndHashCode(of = "id")
@ToString(exclude = { "requestBody", "responseBody", "requestHeaders", "responseHeaders", "metadata" })
public class LogRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "apilogsidseq")
    @SequenceGenerator(name = "apilogsidseq", sequenceName = "apilogsidseq", allocationSize = 1)
    private Long id;

    @Column(name = "endpoint", nullable = false, length = 500)
    private String endpoint;

    @Column(name = "httpmethod", nullable = false, length = 10)
    private String method;

    @Column(name = "statuscode", nullable = false)
    private Integer statusCode;

    @Column(name = "responsetimems", nullable = false)
    private Long responseTimeMs;

    @Column(name = "requestsizebytes")
    private Long requestSizeBytes;

    @Column(name = "responsesizebytes")
    private Long responseSizeBytes;

    @Column(name = "cpuusagepercent")
    private Double cpuUsage;

    @Column(name = "memoryusagepercent")
    private Double memoryUsage;

    @Column(name = "diskiobytes")
    private Long diskIo;

    @Column(name = "networkiobytes")
    private Long networkIo;

    @Column(name = "errorrate")
    private Double errorRate;

    @Column(name = "errorcount")
    private Integer errorCount;

    @Column(name = "errormessage", columnDefinition = "TEXT")
    private String errorMessage;

    @Column(name = "stacktrace", columnDefinition = "TEXT")
    private String stackTrace;

    @Column(name = "requestcount")
    private Integer requestCount;

    @Column(name = "userid", length = 255)
    private String userId;

    @Column(name = "ipaddress")
    private String ipAddress;

    @Column(name = "useragent", columnDefinition = "TEXT")
    private String userAgent;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "requestbody", columnDefinition = "jsonb")
    private Map<String, Object> requestBody;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "responsebody", columnDefinition = "jsonb")
    private Map<String, Object> responseBody;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "requestheaders", columnDefinition = "jsonb")
    private Map<String, Object> requestHeaders;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "responseheaders", columnDefinition = "jsonb")
    private Map<String, Object> responseHeaders;

    @Column(name = "traceid", length = 255)
    private String traceId;

    @Column(name = "spanid", length = 255)
    private String spanId;

    @Column(name = "parentspanid", length = 255)
    private String parentSpanId;

    @Column(name = "servicename", nullable = false, length = 255)
    private String serviceName;

    @Column(name = "serviceversion", length = 50)
    private String serviceVersion;

    @Builder.Default
    @Column(name = "environment", length = 50)
    private String environment = "production";

    @Column(name = "hourofday")
    private Integer hourOfDay;

    @Column(name = "dayofweek")
    private Integer dayOfWeek;

    @Column(name = "isweekend")
    private Boolean isWeekend;

    @Column(name = "isbusinesshours")
    private Boolean isBusinessHours;

    @Builder.Default
    @Column(name = "isprocessed", nullable = false)
    private Boolean isProcessed = false;

    @Column(name = "processedat")
    private LocalDateTime processedAt;

    @Column(name = "anomalydetectionid")
    private Long anomalyDetectionId;

    @Column(name = "mlserviceversion", length = 50)
    private String mlServiceVersion;

    @Column(name = "createdat", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "createdby", length = 255)
    private String createdBy;

    @Column(name = "updatedat")
    private LocalDateTime updatedAt;

    @Column(name = "updatedby", length = 255)
    private String updatedBy;

    @Column(name = "deletedat")
    private LocalDateTime deletedAt;

    @Column(name = "deletedby", length = 255)
    private String deletedBy;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "metadata", columnDefinition = "jsonb")
    private Map<String, Object> metadata;

    @PrePersist
    protected void onCreate() {
        LocalDateTime now = LocalDateTime.now();
        if (createdAt == null)
            createdAt = now;
        if (updatedAt == null)
            updatedAt = now;
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }

    public void markAsProcessed(Long anomalyDetectionId, String mlServiceVersion) {
        this.isProcessed = true;
        this.processedAt = LocalDateTime.now();
        this.anomalyDetectionId = anomalyDetectionId;
        this.mlServiceVersion = mlServiceVersion;
    }

    public void delete(String deletedBy) {
        this.deletedAt = LocalDateTime.now();
        this.deletedBy = deletedBy;
    }

    public boolean isDeleted() {
        return deletedAt != null;
    }
}
