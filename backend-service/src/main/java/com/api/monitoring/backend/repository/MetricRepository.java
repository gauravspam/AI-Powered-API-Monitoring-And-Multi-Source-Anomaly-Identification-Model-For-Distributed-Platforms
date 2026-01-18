package com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.MetricRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface MetricRepository extends JpaRepository<MetricRecord, Long> {

    // Existing methods (used by AnomalyService)
    List<MetricRecord> findByApiIdAndTimestampAfter(Long apiId, LocalDateTime timestamp);
    List<MetricRecord> findByTimestampAfter(LocalDateTime timestamp);
    
    @Query("SELECT DISTINCT m.apiId FROM MetricRecord m")
    List<Long> findDistinctApiIds();
    
    // New methods (for MetricsController)
    List<MetricRecord> findByApiId(Long apiId);
    List<MetricRecord> findTop100ByOrderByTimestampDesc();
}
