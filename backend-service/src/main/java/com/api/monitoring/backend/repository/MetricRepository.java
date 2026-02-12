package com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.MetricRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;

@Repository
public interface MetricRepository extends JpaRepository<MetricRecord, Long> {

    // For Multimodal Windows
    @Query("SELECT m FROM MetricRecord m WHERE m.createdAt >= :start AND m.createdAt < :end ORDER BY m.createdAt ASC")
    List<MetricRecord> findByCreatedAtBetween(@Param("start") Instant start, @Param("end") Instant end);

    // For Controller
    List<MetricRecord> findTop100ByOrderByMetricTimestampDesc();

    List<MetricRecord> findByApiLogId(Long apiLogId);
}
