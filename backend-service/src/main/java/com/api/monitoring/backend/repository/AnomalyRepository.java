package com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.AnomalyRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

public interface AnomalyRepository extends JpaRepository<AnomalyRecord, Long> {

    List<AnomalyRecord> findByEndpoint(String apiName);

    List<AnomalyRecord> findTop100ByEndpointOrderByCreatedAtDesc(String apiName);

    @Query("SELECT a FROM AnomalyRecord a ORDER BY a.createdAt DESC")
    List<AnomalyRecord> findRecentAnomalies();

    // NEW: For getRecentAnomalies() method
    @Query("SELECT a FROM AnomalyRecord a ORDER BY a.createdAt DESC LIMIT 10")
    List<AnomalyRecord> findTop10ByOrderByCreatedAtDesc();

    @Query("SELECT a FROM AnomalyRecord a WHERE a.endpoint = :endpoint " +
            "AND a.createdAt >= :since ORDER BY a.createdAt DESC")
    Optional<AnomalyRecord> findLastScoreByEndpoint(
            @Param("endpoint") String endpoint,
            @Param("since") LocalDateTime since);

    List<AnomalyRecord> findByCreatedAtAfter(LocalDateTime timestamp);


}
