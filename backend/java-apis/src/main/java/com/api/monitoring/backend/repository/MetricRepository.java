package main.java.com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.MetricRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;
import java.time.LocalDateTime;

public interface MetricRepository extends JpaRepository<MetricRecord, UUID> {
    List<MetricRecord> findByApiId(UUID apiId);
    List<MetricRecord> findByApiIdAndTimestampBetween(UUID apiId, LocalDateTime start, LocalDateTime end);
}