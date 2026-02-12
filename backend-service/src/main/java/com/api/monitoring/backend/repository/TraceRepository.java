package com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.TraceRecord;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Repository
public interface TraceRepository extends JpaRepository<TraceRecord, Long> {

    // For Multimodal Windows
    @Query("SELECT t FROM TraceRecord t WHERE t.createdAt >= :start AND t.createdAt < :end ORDER BY t.createdAt ASC")
    List<TraceRecord> findByCreatedAtBetween(@Param("start") Instant start, @Param("end") Instant end);

    // For Controller Pagination
    List<TraceRecord> findAllByOrderByStartTimeDesc(Pageable pageable);

    List<TraceRecord> findByServiceNameOrderByStartTimeDesc(String serviceName, Pageable pageable);

    Optional<TraceRecord> findByTraceId(String traceId);

    // For Stats
    Long countByServiceName(String serviceName);

    @Query("SELECT AVG(t.duration) FROM TraceRecord t WHERE t.serviceName = :serviceName")
    Double averageDurationByServiceName(@Param("serviceName") String serviceName);
}
