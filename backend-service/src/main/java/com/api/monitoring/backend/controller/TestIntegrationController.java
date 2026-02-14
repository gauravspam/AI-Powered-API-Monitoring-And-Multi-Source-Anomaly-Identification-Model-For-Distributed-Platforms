package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.dto.ml.PredictionResponseDto;
import com.api.monitoring.backend.dto.ml.PredictionWindowDto;
import com.api.monitoring.backend.service.MLServiceClient;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@Slf4j
@RestController
@RequestMapping("/api/test-ml")
@RequiredArgsConstructor
public class TestIntegrationController {

    private final MLServiceClient mlServiceClient;

    @PostMapping("/trigger")
    public ResponseEntity<PredictionResponseDto> triggerTest(@RequestBody Map<String, Object> payload) {
        log.info("🚀 Received Simulation Request: {}", payload);

        PredictionWindowDto window;

        // Check if payload comes from Frontend Simulator (flat format)
        if (payload.containsKey("cpuUsage") || payload.containsKey("apiName")) {
            window = generateWindowFromSimulation(payload);
        } else {
            // Fallback for direct API calls or empty body
            window = generateDummyWindow();
        }

        PredictionResponseDto response = mlServiceClient.detectAnomalyDirect(window);

        // FIX: Use getScoreFusion() instead of getFlatFinalScore()
        log.info("✅ ML Prediction Result: IsAnomaly={}, Score={}",
                response.getResult().isAnomaly(),
                response.getResult().getScoreFusion());

        return ResponseEntity.ok(response);
    }

    private PredictionWindowDto generateWindowFromSimulation(Map<String, Object> payload) {
        long now = System.currentTimeMillis();

        // 1. Extract Simulation Values (with defaults)
        String apiName = (String) payload.getOrDefault("apiName", "test-service");
        Double cpuCenter = parseDouble(payload.get("cpuUsage"), 20.0);
        Double memCenter = parseDouble(payload.get("memoryUsage"), 40.0);
        String logLevel = (String) payload.getOrDefault("logLevel", "INFO");
        String logMsg = (String) payload.getOrDefault("logMessage", "Heartbeat check");

        // 2. Build Context
        Map<String, String> context = new HashMap<>();
        context.put("service_name", apiName);
        context.put("window_end_ms", String.valueOf(now));

        // 3. Generate Metric Series (Variance +/- 5.0 around center value)
        List<PredictionWindowDto.MetricSeries> metrics = new ArrayList<>();
        metrics.add(PredictionWindowDto.MetricSeries.builder()
                .name("cpu")
                .values(generateRandomSeries(60, Math.max(0, cpuCenter - 5), Math.min(100, cpuCenter + 5)))
                .build());
        metrics.add(PredictionWindowDto.MetricSeries.builder()
                .name("memory")
                .values(generateRandomSeries(60, Math.max(0, memCenter - 5), Math.min(100, memCenter + 5)))
                .build());

        // 4. Generate Logs (Inject the critical log if simulating attack)
        List<PredictionWindowDto.LogEvent> logs = new ArrayList<>();
        logs.add(PredictionWindowDto.LogEvent.builder()
                .timestamp(now)
                .level(logLevel)
                .message(logMsg)
                .service(apiName)
                .build());

        // 5. Build Final Window
        return PredictionWindowDto.builder()
                .context(context)
                .metrics(metrics)
                .logs(logs)
                .traces(Collections.emptyList()) // Traces optional for this test
                .build();
    }

    private PredictionWindowDto generateDummyWindow() {
        long now = System.currentTimeMillis();
        Map<String, String> context = new HashMap<>();
        context.put("service_name", "test-service-fallback");
        context.put("window_end_ms", String.valueOf(now));

        List<PredictionWindowDto.MetricSeries> metrics = new ArrayList<>();
        metrics.add(PredictionWindowDto.MetricSeries.builder()
                .name("cpu")
                .values(generateRandomSeries(60, 20.0, 40.0))
                .build());

        return PredictionWindowDto.builder()
                .context(context)
                .metrics(metrics)
                .logs(Collections.emptyList())
                .traces(Collections.emptyList())
                .build();
    }

    private List<Double> generateRandomSeries(int count, double min, double max) {
        List<Double> values = new ArrayList<>();
        Random r = new Random();
        for (int i = 0; i < count; i++) {
            values.add(min + (max - min) * r.nextDouble());
        }
        return values;
    }

    private Double parseDouble(Object value, Double defaultValue) {
        if (value instanceof Number)
            return ((Number) value).doubleValue();
        if (value instanceof String) {
            try {
                return Double.parseDouble((String) value);
            } catch (Exception e) {
            }
        }
        return defaultValue;
    }
}
