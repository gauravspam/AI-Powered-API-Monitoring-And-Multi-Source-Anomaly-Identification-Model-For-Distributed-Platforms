package com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.TraceRecord;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface TraceRepository extends JpaRepository<TraceRecord, Long> {
    
    List<TraceRecord> findAllByOrderByTimestampDesc(Pageable pageable);
    
    Optional<TraceRecord> findByTraceId(String traceId);
    
    List<TraceRecord> findByServiceNameOrderByTimestampDesc(String serviceName, Pageable pageable);
    
    Long countByServiceName(String serviceName);
    
    // Use 'duration' not 'durationMs' - it's the Java field name!
    @Query("SELECT AVG(t.duration) FROM TraceRecord t WHERE t.serviceName = :serviceName")
    Double averageDurationByServiceName(@Param("serviceName") String serviceName);
}
