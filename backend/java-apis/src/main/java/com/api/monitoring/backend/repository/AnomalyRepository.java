package main.java.com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.AnomalyRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface AnomalyRepository extends JpaRepository<AnomalyRecord, UUID> {
    List<AnomalyRecord> findByApiName(String apiName);
    List<AnomalyRecord> findTop100ByApiNameOrderByTimestampDesc(String apiName);
    List<AnomalyRecord> findTopNByOrderByTimestampDesc(int n);
}