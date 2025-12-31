package main.java.com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.MetricRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.time.LocalDateTime;

public interface MetricRepository extends JpaRepository<MetricRecord, Long> {
    List<MetricRecord> findByApiId(Long apiId);
    List<MetricRecord> findByApiIdAndTimestampBetween(Long apiId, LocalDateTime start, LocalDateTime end);
}