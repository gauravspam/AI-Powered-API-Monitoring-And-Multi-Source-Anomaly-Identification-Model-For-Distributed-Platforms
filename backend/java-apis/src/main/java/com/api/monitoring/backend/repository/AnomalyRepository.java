package com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.AnomalyRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.time.LocalDateTime;
import java.util.Optional;

public interface AnomalyRepository extends JpaRepository<AnomalyRecord, Long> {
    List<AnomalyRecord> findByApiName(String apiName);

    List<AnomalyRecord> findTop100ByApiNameOrderByTimestampDesc(String apiName);

    List<AnomalyRecord> findTopNByOrderByTimestampDesc(int n);

    // NEW: For fallback prediction (Phase 2)
    @Query("SELECT a FROM AnomalyRecord a WHERE a.apiName = :apiName " +
            "AND a.timestamp >= :since ORDER BY a.timestamp DESC")
    Optional<AnomalyRecord> findLastScoreByEndpoint(
            @Param("apiName") String apiName,
            @Param("since") LocalDateTime since);
}
