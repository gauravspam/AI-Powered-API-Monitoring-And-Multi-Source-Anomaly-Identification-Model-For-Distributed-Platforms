package com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.MetricRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface MetricRepository extends JpaRepository<MetricRecord, Long> {

    /**
     * Find metrics by API ID after a certain timestamp
     */
    List<MetricRecord> findByApiIdAndTimestampAfter(Long apiId, LocalDateTime timestamp);

    /**
     * Find metrics after a certain timestamp (for all APIs)
     */
    List<MetricRecord> findByTimestampAfter(LocalDateTime timestamp);

    /**
     * Get distinct API IDs
     */
    @Query("SELECT DISTINCT m.apiId FROM MetricRecord m")
    List<Long> findDistinctApiIds();

    /**
     * Count total metrics
     */
    long count();
}
