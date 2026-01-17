package com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.AnomalyRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

public interface AnomalyRepository extends JpaRepository<AnomalyRecord, Long> {

    List<AnomalyRecord> findByApiName(String apiName);

    List<AnomalyRecord> findTop100ByApiNameOrderByTimestampDesc(String apiName);

    @Query("SELECT a FROM AnomalyRecord a ORDER BY a.timestamp DESC")
    List<AnomalyRecord> findRecentAnomalies();
    
    // NEW: For getRecentAnomalies() method
    @Query("SELECT a FROM AnomalyRecord a ORDER BY a.timestamp DESC LIMIT 10")
    List<AnomalyRecord> findTop10ByOrderByTimestampDesc();

    @Query("SELECT a FROM AnomalyRecord a WHERE a.apiName = :apiName " +
            "AND a.timestamp >= :since ORDER BY a.timestamp DESC")
    Optional<AnomalyRecord> findLastScoreByEndpoint(
            @Param("apiName") String apiName,
            @Param("since") LocalDateTime since);

    List<AnomalyRecord> findByTimestampAfter(LocalDateTime timestamp);
}
