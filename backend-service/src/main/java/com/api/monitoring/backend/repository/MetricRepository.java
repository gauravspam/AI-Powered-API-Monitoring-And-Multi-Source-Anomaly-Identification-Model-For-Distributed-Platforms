package com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.MetricRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.time.LocalDateTime;
import java.util.List;

public interface MetricRepository extends JpaRepository<MetricRecord, Long> {

    List<MetricRecord> findByApiLogIdAndMetricTimestampAfter(Long apiLogId, LocalDateTime timestamp);

    List<MetricRecord> findByMetricTimestampAfter(LocalDateTime timestamp);

    @Query("SELECT DISTINCT m.apiLogId FROM MetricRecord m")
    List<Long> findDistinctApiLogIds();

    List<MetricRecord> findByApiLogId(Long apiLogId);

    List<MetricRecord> findTop100ByOrderByMetricTimestampDesc();
}
