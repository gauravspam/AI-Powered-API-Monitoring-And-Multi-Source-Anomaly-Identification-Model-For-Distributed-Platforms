package com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.LogRecord;
import jakarta.transaction.Transactional;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

/**
 * Repository for LogRecord entities
 * Provides query methods for API log data
 */
@Repository
public interface LogRepository
    extends JpaRepository<LogRecord, Long>, JpaSpecificationExecutor<LogRecord>
{
    // ============= BASIC QUERIES =============

    /**
     * Find logs by endpoint
     */
    List<LogRecord> findByEndpointOrderByCreatedAtDesc(String endpoint);

    Page<LogRecord> findByEndpointOrderByCreatedAtDesc(
        String endpoint,
        Pageable pageable
    );

    /**
     * Find logs by status code
     */
    List<LogRecord> findByStatusCodeOrderByCreatedAtDesc(Integer statusCode);

    /**
     * Find error logs (status >= 400)
     */
    @Query(
        "SELECT l FROM LogRecord l WHERE l.statusCode >= 400 ORDER BY l.createdAt DESC"
    )
    List<LogRecord> findErrorLogs();

    Page<LogRecord> findByStatusCodeGreaterThanEqualOrderByCreatedAtDesc(
        Integer statusCode,
        Pageable pageable
    );

    /**
     * Find logs by time range
     */
    List<LogRecord> findByCreatedAtBetweenOrderByCreatedAtDesc(
        LocalDateTime start,
        LocalDateTime end
    );

    Page<LogRecord> findByCreatedAtBetweenOrderByCreatedAtDesc(
        LocalDateTime start,
        LocalDateTime end,
        Pageable pageable
    );

    /**
     * Find recent logs
     */
    List<LogRecord> findByCreatedAtAfterOrderByCreatedAtDesc(
        LocalDateTime after
    );

    Page<LogRecord> findByCreatedAtAfterOrderByCreatedAtDesc(
        LocalDateTime after,
        Pageable pageable
    );

    /**
     * Find logs by trace ID
     */
    List<LogRecord> findByTraceIdOrderByCreatedAtAsc(String traceId);

    /**
     * Find logs by environment
     */
    List<LogRecord> findByEnvironmentOrderByCreatedAtDesc(String environment);

    // ============= ML PROCESSING QUERIES (Priority 1) =============

    /**
     * Find all unprocessed logs (not yet analyzed by ML service)
     */
    List<LogRecord> findByProcessedFalseOrderByCreatedAtAsc();

    /**
     * Find unprocessed logs with pagination
     */
    Page<LogRecord> findByProcessedFalseOrderByCreatedAtAsc(Pageable pageable);

    /**
     * Find unprocessed logs created before a certain time
     */
    List<LogRecord> findByProcessedFalseAndCreatedAtBeforeOrderByCreatedAtAsc(
        LocalDateTime before
    );

    /**
     * Find unprocessed logs that don't have ML version set
     */
    List<LogRecord> findByProcessedFalseAndMlServiceVersionIsNull();

    /**
     * Count unprocessed logs
     */
    long countByProcessedFalse();

    /**
     * Count logs by processing status
     */
    long countByProcessed(Boolean processed);

    /**
     * Find logs that have been processed and have anomaly results
     */
    List<LogRecord> findByAnomalyIdIsNotNull();

    Page<LogRecord> findByAnomalyIdIsNotNullOrderByProcessedAtDesc(
        Pageable pageable
    );

    /**
     * Find logs processed after a certain time
     */
    List<
        LogRecord
    > findByProcessedTrueAndProcessedAtAfterOrderByProcessedAtDesc(
        LocalDateTime after
    );

    /**
     * Find logs by endpoint that haven't been processed
     */
    List<LogRecord> findByEndpointAndProcessedFalseOrderByCreatedAtAsc(
        String endpoint
    );

    /**
     * Find oldest unprocessed logs (for batch processing)
     */
    @Query(
        "SELECT l FROM LogRecord l WHERE l.processed = false " +
            "ORDER BY l.createdAt ASC"
    )
    List<LogRecord> findOldestUnprocessedLogs(Pageable pageable);

    /**
     * Find unprocessed error logs (status code >= 400)
     */
    @Query(
        "SELECT l FROM LogRecord l WHERE l.processed = false " +
            "AND l.statusCode >= 400 " +
            "ORDER BY l.createdAt ASC"
    )
    List<LogRecord> findUnprocessedErrors();

    /**
     * Find unprocessed slow requests
     */
    @Query(
        "SELECT l FROM LogRecord l WHERE l.processed = false " +
            "AND l.responseTimeMs > :thresholdMs " +
            "ORDER BY l.createdAt ASC"
    )
    List<LogRecord> findUnprocessedSlowRequests(
        @Param("thresholdMs") Long thresholdMs
    );

    /**
     * Mark log as processed (update query)
     */
    @Transactional
    @Modifying
    @Query(
        "UPDATE LogRecord l SET l.processed = true, l.processedAt = :processedAt, " +
            "l.anomalyId = :anomalyId, l.mlServiceVersion = :version " +
            "WHERE l.id = :logId"
    )
    int markAsProcessed(
        @Param("logId") Long logId,
        @Param("processedAt") LocalDateTime processedAt,
        @Param("anomalyId") Long anomalyId,
        @Param("version") String version
    );

    /**
     * Batch mark logs as processed
     */
    @Transactional
    @Modifying
    @Query(
        "UPDATE LogRecord l SET l.processed = true, l.processedAt = :processedAt " +
            "WHERE l.id IN :logIds"
    )
    int batchMarkAsProcessed(
        @Param("logIds") List<Long> logIds,
        @Param("processedAt") LocalDateTime processedAt
    );

    // ============= STATISTICS & ANALYTICS QUERIES =============

    /**
     * Count logs by endpoint
     */
    long countByEndpoint(String endpoint);

    long countByEndpointAndCreatedAtAfter(String endpoint, LocalDateTime after);

    /**
     * Count error logs
     */
    @Query("SELECT COUNT(l) FROM LogRecord l WHERE l.statusCode >= 400")
    long countErrors();

    @Query(
        "SELECT COUNT(l) FROM LogRecord l WHERE l.statusCode >= 400 " +
            "AND l.createdAt >= :since"
    )
    long countErrorsSince(@Param("since") LocalDateTime since);

    /**
     * Calculate average response time
     */
    @Query(
        "SELECT AVG(l.responseTimeMs) FROM LogRecord l WHERE l.endpoint = :endpoint " +
            "AND l.createdAt >= :since"
    )
    Double calculateAverageResponseTime(
        @Param("endpoint") String endpoint,
        @Param("since") LocalDateTime since
    );

    /**
     * Find slow requests (above threshold)
     */
    @Query(
        "SELECT l FROM LogRecord l WHERE l.responseTimeMs > :thresholdMs " +
            "AND l.createdAt >= :since " +
            "ORDER BY l.responseTimeMs DESC"
    )
    List<LogRecord> findSlowRequests(
        @Param("thresholdMs") Long thresholdMs,
        @Param("since") LocalDateTime since
    );

    /**
     * Group logs by endpoint with statistics
     */
    @Query(
        "SELECT l.endpoint, COUNT(l), AVG(l.responseTimeMs), " +
            "SUM(CASE WHEN l.statusCode >= 400 THEN 1 ELSE 0 END) " +
            "FROM LogRecord l WHERE l.createdAt >= :since " +
            "GROUP BY l.endpoint"
    )
    List<Object[]> getEndpointStatistics(@Param("since") LocalDateTime since);

    /**
     * Count logs by hour of day
     */
    @Query(
        "SELECT l.hourOfDay, COUNT(l) FROM LogRecord l " +
            "WHERE l.createdAt >= :since " +
            "GROUP BY l.hourOfDay " +
            "ORDER BY l.hourOfDay"
    )
    List<Object[]> countByHourOfDay(@Param("since") LocalDateTime since);

    /**
     * Find high-traffic endpoints
     */
    @Query(
        "SELECT l.endpoint, COUNT(l) as cnt FROM LogRecord l " +
            "WHERE l.createdAt >= :since " +
            "GROUP BY l.endpoint " +
            "ORDER BY cnt DESC"
    )
    List<Object[]> findHighTrafficEndpoints(
        @Param("since") LocalDateTime since,
        Pageable pageable
    );

    /**
     * Calculate error rate by endpoint
     */
    @Query(
        "SELECT l.endpoint, " +
            "CAST(SUM(CASE WHEN l.statusCode >= 400 THEN 1 ELSE 0 END) AS double) / COUNT(l) " +
            "FROM LogRecord l WHERE l.createdAt >= :since " +
            "GROUP BY l.endpoint"
    )
    List<Object[]> calculateErrorRateByEndpoint(
        @Param("since") LocalDateTime since
    );

    // ============= DASHBOARD QUERIES =============

    /**
     * Get recent activity summary
     */
    @Query(
        "SELECT COUNT(l), AVG(l.responseTimeMs), " +
            "SUM(CASE WHEN l.statusCode >= 400 THEN 1 ELSE 0 END) " +
            "FROM LogRecord l WHERE l.createdAt >= :since"
    )
    Object[] getActivitySummary(@Param("since") LocalDateTime since);

    /**
     * Find logs for dashboard (recent, with pagination)
     */
    @Query(
        "SELECT l FROM LogRecord l WHERE l.createdAt >= :since " +
            "ORDER BY l.createdAt DESC"
    )
    List<LogRecord> findDashboardLogs(
        @Param("since") LocalDateTime since,
        Pageable pageable
    );

    /**
     * Count logs by status code range
     */
    @Query(
        "SELECT CASE " +
            "WHEN l.statusCode < 300 THEN 'success' " +
            "WHEN l.statusCode < 400 THEN 'redirect' " +
            "WHEN l.statusCode < 500 THEN 'client_error' " +
            "ELSE 'server_error' END as category, " +
            "COUNT(l) " +
            "FROM LogRecord l WHERE l.createdAt >= :since " +
            "GROUP BY category"
    )
    List<Object[]> countByStatusCategory(@Param("since") LocalDateTime since);
}
