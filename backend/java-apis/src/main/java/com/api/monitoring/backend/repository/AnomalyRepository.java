package com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.AnomalyRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

public interface AnomalyRepository extends JpaRepository<AnomalyRecord, Long> {

    // Existing methods
    List<AnomalyRecord> findByApiName(String apiName);

    List<AnomalyRecord> findTop100ByApiNameOrderByTimestampDesc(String apiName);

    // FIXED: Use @Query annotation instead of method name parsing
    @Query("SELECT a FROM AnomalyRecord a ORDER BY a.timestamp DESC")
    List<AnomalyRecord> findRecentAnomalies();

    // For fallback prediction (Phase 2)
    @Query("SELECT a FROM AnomalyRecord a WHERE a.apiName = :apiName " +
            "AND a.timestamp >= :since ORDER BY a.timestamp DESC")
    Optional<AnomalyRecord> findLastScoreByEndpoint(
            @Param("apiName") String apiName,
            @Param("since") LocalDateTime since);

    // NEW: Find by timestamp after (for AnomalyDetectionJob)
    List<AnomalyRecord> findByTimestampAfter(LocalDateTime timestamp);
}
