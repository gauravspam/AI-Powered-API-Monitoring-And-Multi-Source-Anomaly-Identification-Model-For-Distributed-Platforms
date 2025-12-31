package com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.AnomalyRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface AnomalyRepository extends JpaRepository<AnomalyRecord, Long> {
    List<AnomalyRecord> findByApiName(String apiName);
    List<AnomalyRecord> findTop100ByApiNameOrderByTimestampDesc(String apiName);
    List<AnomalyRecord> findTopNByOrderByTimestampDesc(int n);
}