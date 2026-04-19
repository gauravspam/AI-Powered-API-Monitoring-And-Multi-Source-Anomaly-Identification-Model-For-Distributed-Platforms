package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.model.AnomalyRecord;
import com.api.monitoring.backend.model.MetricRecord;
import com.api.monitoring.backend.repository.AnomalyRepository;
import com.api.monitoring.backend.repository.MetricRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.ThreadLocalRandom;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
public class ServicesController {

    private static final double HEALTHY_ERROR_RATE_THRESHOLD = 0.05;
    private static final double DEGRADED_ERROR_RATE_THRESHOLD = 0.15;
    private static final long HEALTHY_ANOMALY_COUNT_THRESHOLD = 5;
    private static final long DEGRADED_ANOMALY_COUNT_THRESHOLD = 20;

    private final MetricRepository metricRepository;
    private final AnomalyRepository anomalyRepository;

    public ServicesController(MetricRepository metricRepository, AnomalyRepository anomalyRepository) {
        this.metricRepository = metricRepository;
        this.anomalyRepository = anomalyRepository;
    }

    @GetMapping("/services")
    public ResponseEntity<List<Map<String, Object>>> getServices() {
        List<MetricRecord> metrics = metricRepository.findTop100ByOrderByMetricTimestampDesc();
        
        if (metrics.isEmpty()) {
            return ResponseEntity.ok(getDefaultServices());
        }

        Map<String, List<MetricRecord>> byService = metrics.stream()
                .filter(m -> m.getServiceName() != null && !m.getServiceName().isBlank())
                .collect(Collectors.groupingBy(MetricRecord::getServiceName));

        List<AnomalyRecord> anomalies = anomalyRepository.findRecentAnomalies();
        Map<String, Long> anomalyCountByService = anomalies.stream()
                .filter(a -> a.getServiceName() != null)
                .collect(Collectors.groupingBy(AnomalyRecord::getServiceName, Collectors.counting()));

        List<Map<String, Object>> services = new ArrayList<>();
        long serviceId = 1;
        
        for (Map.Entry<String, List<MetricRecord>> entry : byService.entrySet()) {
            String serviceName = entry.getKey();
            List<MetricRecord> serviceMetrics = entry.getValue();

            double avgLatency = serviceMetrics.stream()
                    .filter(m -> m.getResponseTimeMs() != null)
                    .mapToLong(MetricRecord::getResponseTimeMs)
                    .average()
                    .orElse(0.0);

                List<Long> latencySeries = serviceMetrics.stream()
                    .map(MetricRecord::getResponseTimeMs)
                    .filter(Objects::nonNull)
                    .sorted()
                    .collect(Collectors.toList());
                long p99Latency = latencySeries.isEmpty()
                    ? Math.round(avgLatency)
                    : latencySeries.get(Math.min((int) Math.floor(latencySeries.size() * 0.99), latencySeries.size() - 1));

            double avgErrorRate = serviceMetrics.stream()
                    .filter(m -> m.getErrorRate() != null)
                    .mapToDouble(MetricRecord::getErrorRate)
                    .average()
                    .orElse(0.0);

            long totalRequests = serviceMetrics.stream()
                    .filter(m -> m.getRequestCount() != null)
                    .mapToLong(MetricRecord::getRequestCount)
                    .sum();

            int reqPerMin = (int) (totalRequests / Math.max(1, serviceMetrics.size()));
            long anomaliesCount = anomalyCountByService.getOrDefault(serviceName, 0L);
            double anomalyRate = serviceMetrics.isEmpty() ? 0.0 : (double) anomaliesCount / serviceMetrics.size();

            String status = resolveStatus(avgErrorRate, anomaliesCount);

            Map<String, Object> service = new HashMap<>();
            service.put("id", serviceId++);
            service.put("name", serviceName);
            service.put("ownerTeam", "Platform Team");
            service.put("environment", "production");
            service.put("status", status);
            service.put("p99LatencyMs", p99Latency);
            service.put("avgLatencyMs", Math.round(avgLatency));
            service.put("errorRate", Math.round(avgErrorRate * 1000.0) / 1000.0);
            service.put("anomalyRate", Math.round(Math.min(1.0, anomalyRate) * 1000.0) / 1000.0);
            service.put("lastDeploymentAt", LocalDateTime.now().minusDays(ThreadLocalRandom.current().nextInt(30)).toString());
            service.put("requestPerMin", reqPerMin);
            service.put("tags", Arrays.asList("api", "monitoring"));
            
            services.add(service);
        }

        return ResponseEntity.ok(services.isEmpty() ? getDefaultServices() : services);
    }

    private List<Map<String, Object>> getDefaultServices() {
        List<Map<String, Object>> services = new ArrayList<>();
        
        Map<String, Object> svc1 = new HashMap<>();
        svc1.put("id", 1);
        svc1.put("name", "api-gateway");
        svc1.put("ownerTeam", "Platform Team");
        svc1.put("environment", "production");
        svc1.put("status", "healthy");
        svc1.put("p99LatencyMs", 82);
        svc1.put("avgLatencyMs", 45);
        svc1.put("errorRate", 0.02);
        svc1.put("anomalyRate", 0.10);
        svc1.put("lastDeploymentAt", LocalDateTime.now().minusDays(5).toString());
        svc1.put("requestPerMin", 1200);
        svc1.put("tags", Arrays.asList("api", "gateway"));
        services.add(svc1);
        
        Map<String, Object> svc2 = new HashMap<>();
        svc2.put("id", 2);
        svc2.put("name", "user-service");
        svc2.put("ownerTeam", "Identity Team");
        svc2.put("environment", "production");
        svc2.put("status", "healthy");
        svc2.put("p99LatencyMs", 61);
        svc2.put("avgLatencyMs", 32);
        svc2.put("errorRate", 0.01);
        svc2.put("anomalyRate", 0.05);
        svc2.put("lastDeploymentAt", LocalDateTime.now().minusDays(2).toString());
        svc2.put("requestPerMin", 850);
        svc2.put("tags", Arrays.asList("api", "users"));
        services.add(svc2);
        
        Map<String, Object> svc3 = new HashMap<>();
        svc3.put("id", 3);
        svc3.put("name", "payment-service");
        svc3.put("ownerTeam", "Finance Team");
        svc3.put("environment", "production");
        svc3.put("status", "degraded");
        svc3.put("p99LatencyMs", 610);
        svc3.put("avgLatencyMs", 180);
        svc3.put("errorRate", 0.08);
        svc3.put("anomalyRate", 0.25);
        svc3.put("lastDeploymentAt", LocalDateTime.now().minusDays(1).toString());
        svc3.put("requestPerMin", 450);
        svc3.put("tags", Arrays.asList("api", "payments"));
        services.add(svc3);
        
        return services;
    }

    @GetMapping("/dashboard/anomalies")
    public ResponseEntity<List<Map<String, Object>>> getDashboardAnomalies(
            @RequestParam(defaultValue = "50") int limit) {
        List<AnomalyRecord> anomalies = anomalyRepository.findRecentAnomalies();
        
        List<Map<String, Object>> result = anomalies.stream()
                .limit(limit)
                .map(a -> {
                    Map<String, Object> map = new HashMap<>();
                    map.put("id", a.getId());
                    map.put("serviceName", a.getServiceName() != null ? a.getServiceName() : "unknown");
                    map.put("endpoint", a.getEndpoint());
                    map.put("severity", a.getSeverity() != null ? a.getSeverity().toLowerCase() : "medium");
                    map.put("score", a.getHybridEnsembleScore());
                    map.put("status", a.getStatus() != null ? a.getStatus().toLowerCase() : "active");
                    return map;
                })
                .collect(Collectors.toList());

        return ResponseEntity.ok(result);
    }

    private String resolveStatus(double avgErrorRate, long anomaliesCount) {
        if (avgErrorRate < HEALTHY_ERROR_RATE_THRESHOLD && anomaliesCount < HEALTHY_ANOMALY_COUNT_THRESHOLD) {
            return "healthy";
        }
        if (avgErrorRate < DEGRADED_ERROR_RATE_THRESHOLD && anomaliesCount < DEGRADED_ANOMALY_COUNT_THRESHOLD) {
            return "degraded";
        }
        return "down";
    }
}
