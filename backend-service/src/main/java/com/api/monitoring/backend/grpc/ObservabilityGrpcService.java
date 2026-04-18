package com.api.monitoring.backend.grpc;

import com.api.monitoring.backend.dto.MetricIngestionDTO;
import com.api.monitoring.backend.dto.LogDTO;
import com.api.monitoring.backend.dto.TraceDTO;
import com.api.monitoring.backend.model.MetricRecord;
import com.api.monitoring.backend.model.LogRecord;
import com.api.monitoring.backend.model.TraceRecord;
import com.api.monitoring.backend.repository.MetricRepository;
import com.api.monitoring.backend.repository.LogRepository;
import com.api.monitoring.backend.repository.TraceRepository;
import com.api.monitoring.backend.service.OpenSearchLogService;
import io.grpc.stub.StreamObserver;
import net.devh.boot.grpc.server.service.GrpcService;
import observability.Observability;
import observability.ObservabilityServiceGrpc;
import org.springframework.beans.factory.annotation.Autowired;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@GrpcService
public class ObservabilityGrpcService extends ObservabilityServiceGrpc.ObservabilityServiceImplBase {

    @Autowired
    private MetricRepository metricRepository;

    @Autowired
    private LogRepository logRepository;

    @Autowired
    private TraceRepository traceRepository;

    @Autowired
    private OpenSearchLogService openSearchLogService;

    @Override
    public void ingest(Observability.IngestRequest request, StreamObserver<Observability.IngestResponse> responseObserver) {
        Observability.IngestResponse.Builder response = Observability.IngestResponse.newBuilder();
        
        try {
            if (request.hasLogs()) {
                Observability.LogBatchRequest logs = request.getLogs();
                int count = 0;
                for (Observability.LogEntry entry : logs.getLogsList()) {
                    saveLog(entry);
                    count++;
                }
                response.setSuccess(true)
                       .setMessage("Ingested " + count + " logs")
                       .setReceivedCount(count);
            } else if (request.hasMetrics()) {
                Observability.MetricBatchRequest metrics = request.getMetrics();
                int count = 0;
                for (Observability.MetricEntry entry : metrics.getMetricsList()) {
                    saveMetric(entry);
                    count++;
                }
                response.setSuccess(true)
                       .setMessage("Ingested " + count + " metrics")
                       .setReceivedCount(count);
            } else if (request.hasTraces()) {
                Observability.TraceBatchRequest traces = request.getTraces();
                int count = 0;
                for (Observability.TraceEntry entry : traces.getTracesList()) {
                    saveTrace(entry);
                    count++;
                }
                response.setSuccess(true)
                       .setMessage("Ingested " + count + " traces")
                       .setReceivedCount(count);
            } else {
                response.setSuccess(false)
                       .setMessage("No data provided");
            }
        } catch (Exception e) {
            response.setSuccess(false)
                   .setMessage("Error: " + e.getMessage());
        }
        
        responseObserver.onNext(response.build());
        responseObserver.onCompleted();
    }

    @Override
    public void healthCheck(Observability.HealthRequest request, StreamObserver<Observability.HealthResponse> responseObserver) {
        responseObserver.onNext(Observability.HealthResponse.newBuilder()
                .setStatus("UP")
                .setVersion("1.0.0")
                .setUptimeSeconds(System.currentTimeMillis() / 1000)
                .build());
        responseObserver.onCompleted();
    }

    public void ingestMetric(Observability.MetricEntry entry) {
        saveMetric(entry);
    }

    public void ingestLog(Observability.LogEntry entry) {
        saveLog(entry);
    }

    public void ingestTrace(Observability.TraceEntry entry) {
        saveTrace(entry);
    }

    private void saveMetric(Observability.MetricEntry entry) {
        MetricRecord record = new MetricRecord();
        record.setServiceName(entry.getServiceName());
        record.setCpuUsagePercent(entry.getCpuUsage());
        record.setMemoryUsagePercent(entry.getMemoryUsage());
        record.setDiskIoBytes(entry.getDiskIoBytes());
        record.setNetworkIoBytes(entry.getNetworkIoBytes());
        record.setResponseTimeMs(entry.getResponseTimeMs());
        record.setRequestCount((int) entry.getRequestCount());
        record.setErrorRate(entry.getErrorRate());
        record.setEnvironment(entry.getEnvironment());
        record.setMetricTimestamp(LocalDateTime.now());
        record.setCreatedAt(LocalDateTime.now());
        metricRepository.save(record);
    }

    private void saveLog(Observability.LogEntry entry) {
        LogRecord record = new LogRecord();
        record.setServiceName(entry.getServiceName());
        record.setMethod("gRPC");
        record.setStatusCode(0);
        record.setResponseTimeMs(0L);
        record.setTraceId(entry.getTraceId());
        record.setSpanId(entry.getSpanId());
        record.setEnvironment(entry.getEnvironment());
        record.setCreatedAt(LocalDateTime.now());

        Map<String, Object> metadata = new HashMap<>();
        metadata.put("level", entry.getLevel());
        metadata.put("message", entry.getMessage());
        if (entry.getMetadataCount() > 0) {
            metadata.put("protoMetadata", entry.getMetadataMap());
        }
        record.setMetadata(metadata);

        logRepository.save(record);

        try {
            LogDTO dto = new LogDTO();
            dto.setServiceName(entry.getServiceName());
            dto.setLevel(entry.getLevel());
            dto.setMessage(entry.getMessage());
            dto.setTraceId(entry.getTraceId());
            dto.setSpanId(entry.getSpanId());
            dto.setEnvironment(entry.getEnvironment());
            dto.setSource("grpc");
            openSearchLogService.indexLog(dto);
        } catch (Exception e) {
            System.err.println("Failed to index to OpenSearch: " + e.getMessage());
        }
    }

    private void saveTrace(Observability.TraceEntry entry) {
        TraceRecord record = new TraceRecord();
        record.setTraceId(entry.getTraceId());
        record.setSpanId(entry.getSpanId());
        record.setParentSpanId(entry.getParentSpanId());
        record.setServiceName(entry.getServiceName());
        record.setOperationName(entry.getOperationName());
        record.setDuration(entry.getDurationMs());
        record.setStatusCode(entry.getStatusCode());
        record.setIsError(entry.getStatusCode() >= 400);
        record.setStartTime(LocalDateTime.now());
        record.setCreatedAt(LocalDateTime.now());

        if (entry.getTagsCount() > 0) {
            record.setTags(new HashMap<>(entry.getTagsMap()));
        }

        traceRepository.save(record);
    }
}