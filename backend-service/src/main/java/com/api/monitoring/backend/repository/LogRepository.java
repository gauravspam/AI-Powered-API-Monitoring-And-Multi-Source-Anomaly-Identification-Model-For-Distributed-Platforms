package com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.LogRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;

@Repository
public interface LogRepository extends JpaRepository<LogRecord, Long> {

    /**
     * Find logs within time window (for multimodal windows).
     */
    @Query("SELECT l FROM LogRecord l WHERE l.createdAt >= :start AND l.createdAt < :end ORDER BY l.createdAt ASC")
    List<LogRecord> findByCreatedAtBetween(
            @Param("start") Instant start,
            @Param("end") Instant end);

}
