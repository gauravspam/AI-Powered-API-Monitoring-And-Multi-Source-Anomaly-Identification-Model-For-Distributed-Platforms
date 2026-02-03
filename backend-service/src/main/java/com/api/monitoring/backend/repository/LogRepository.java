package com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.LogRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface LogRepository extends JpaRepository<LogRecord, Long> {
    // Minimal repository for now.
    // We removed all derived query methods that assumed fields like `timestamp` or
    // `anomalyId`.
    // Add specific queries later once LogRecord fields are finalized.
}
