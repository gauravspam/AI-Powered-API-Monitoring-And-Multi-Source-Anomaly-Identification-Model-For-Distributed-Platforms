package com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.AnomalyRecord;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface AnomalyRepository extends JpaRepository<AnomalyRecord, Long> {
    // Find recent anomalies
    @Query(
        "SELECT a FROM AnomalyRecord a WHERE a.createdAt >= :since ORDER BY a.createdAt DESC"
    )
    List<AnomalyRecord> findRecentAnomalies(
        @Param("since") LocalDateTime since
    );

    // Find by severity
    List<AnomalyRecord> findBySeverityOrderByCreatedAtDesc(String severity);

    // Find by severity list
    Page<AnomalyRecord> findBySeverityInOrderByCreatedAtDesc(
        List<String> severities,
        Pageable pageable
    );

    // Find unacknowledged critical
    @Query(
        "SELECT a FROM AnomalyRecord a WHERE a.acknowledged = false AND a.severity IN ('CRITICAL', 'HIGH') ORDER BY a.createdAt DESC"
    )
    List<AnomalyRecord> findUnacknowledgedCritical();

    // Count by severity and date
    long countBySeverityAndCreatedAtAfter(String severity, LocalDateTime since);

    // Count by date (all severities)
    long countByCreatedAtAfter(LocalDateTime since);

    // Find by endpoint
    List<AnomalyRecord> findByEndpointOrderByCreatedAtDesc(String endpoint);

    // Find active anomalies
    @Query(
        "SELECT a FROM AnomalyRecord a WHERE a.status = 'ACTIVE' ORDER BY a.createdAt DESC"
    )
    List<AnomalyRecord> findActiveAnomalies();
}
