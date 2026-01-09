package com.api.monitoring.repository;

import com.api.monitoring.entity.AnomalyScore;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Repository for AnomalyScore entity
 */
@Repository
public interface AnomalyScoreRepository extends JpaRepository<AnomalyScore, Long> {
    
    List<AnomalyScore> findByApiEndpointOrderByTimestampDesc(
        String endpoint, Pageable pageable);
    
    List<AnomalyScore> findByAnomalyTypeOrderByTimestampDesc(
        String anomalyType, Pageable pageable);
    
    List<AnomalyScore> findBySeverityOrderByTimestampDesc(
        String severity, Pageable pageable);
    
    @Query("SELECT a FROM AnomalyScore a " +
           "WHERE a.timestamp >= :startTime " +
           "ORDER BY a.score DESC")
    List<AnomalyScore> findHighestScoresAfter(
        @Param("startTime") LocalDateTime startTime, 
        Pageable pageable);
    
    @Query("SELECT a FROM AnomalyScore a " +
           "WHERE a.apiEndpoint = :endpoint " +
           "AND a.timestamp BETWEEN :startTime AND :endTime " +
           "ORDER BY a.timestamp DESC")
    List<AnomalyScore> findByEndpointAndTimeRange(
        @Param("endpoint") String endpoint,
        @Param("startTime") LocalDateTime startTime,
        @Param("endTime") LocalDateTime endTime,
        Pageable pageable);
    
    @Query("SELECT COUNT(a) FROM AnomalyScore a " +
           "WHERE a.severity = :severity " +
           "AND a.timestamp >= :startTime")
    long countBySeverityAndTimeRange(
        @Param("severity") String severity,
        @Param("startTime") LocalDateTime startTime);
    
    @Query("SELECT AVG(a.score) FROM AnomalyScore a " +
           "WHERE a.apiEndpoint = :endpoint " +
           "AND a.timestamp >= :startTime")
    Double getAverageScoreForEndpoint(
        @Param("endpoint") String endpoint,
        @Param("startTime") LocalDateTime startTime);
    
    @Query("SELECT COUNT(a) FROM AnomalyScore a " +
           "WHERE a.timestamp >= :startTime")
    long countSince(@Param("startTime") LocalDateTime startTime);
}