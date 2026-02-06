package com.api.monitoring.backend.util;

import com.api.monitoring.backend.dto.FeatureWindow;
import com.api.monitoring.backend.model.MetricRecord;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Extracts time-series features from MetricRecord for ML models
 * - MSIF-LSTM: 60-minute window, 1-min buckets, 5 metrics
 * - PLE-GRU: 24-hour window, 1-min buckets, 7 features (5 metrics + 2 time)
 */
@Component
public class FeatureEngineer {

    /**
     * Build MSIF features: 60-minute window, 5 metrics per minute
     * Metrics: [responseTimeMs, errorRate, requestCount, cpuUsage, memoryUsage]
     */
    public List<Double[]> buildMsifFeatures(List<MetricRecord> metrics) {
        List<Double[]> msifFeatures = new ArrayList<>();

        // Group metrics into 1-minute buckets (60 total)
        Map<Integer, List<MetricRecord>> minuteBuckets = new TreeMap<>();
        for (int i = 0; i < 60; i++) {
            minuteBuckets.put(i, new ArrayList<>());
        }

        if (metrics.isEmpty()) {
            // Return zero-filled features
            for (int i = 0; i < 60; i++) {
                msifFeatures.add(new Double[] { 0.0, 0.0, 0.0, 0.0, 0.0 });
            }
            return msifFeatures;
        }

        LocalDateTime baseTime = metrics.get(0).getMetricTimestamp();

        // Distribute metrics into buckets
        for (MetricRecord metric : metrics) {
            long minutesDiff = ChronoUnit.MINUTES.between(baseTime, metric.getMetricTimestamp());
            if (minutesDiff >= 0 && minutesDiff < 60) {
                minuteBuckets.get((int) minutesDiff).add(metric);
            }
        }

        // Extract 5 metrics per minute
        for (int minute = 0; minute < 60; minute++) {
            List<MetricRecord> bucket = minuteBuckets.get(minute);
            Double[] features = new Double[5];

            if (bucket.isEmpty()) {
                // Zero-fill empty buckets
                Arrays.fill(features, 0.0);
            } else {
                features[0] = calculateAvgResponseTime(bucket); // Avg response time
                features[1] = calculateAvgErrorRate(bucket); // Avg error rate
                features[2] = calculateTotalRequests(bucket); // Total requests
                features[3] = calculateAvgCpuUsage(bucket); // Avg CPU usage
                features[4] = calculateAvgMemoryUsage(bucket); // Avg memory usage
            }

            // Normalize to [0, 1]
            features = normalizeMetrics(features);
            msifFeatures.add(features);
        }

        return msifFeatures;
    }

    /**
     * Build PLE features: 24-hour window, 7 features per minute
     * Features: [responseTimeMs, errorRate, requestCount, cpuUsage, memoryUsage,
     * hour_of_day, day_of_week]
     */
    public List<Double[]> buildPleFeatures(List<MetricRecord> metrics, LocalDateTime now) {
        List<Double[]> pleFeatures = new ArrayList<>();

        // 1440 minutes in 24 hours
        Map<Integer, List<MetricRecord>> minuteBuckets = new TreeMap<>();
        for (int i = 0; i < 1440; i++) {
            minuteBuckets.put(i, new ArrayList<>());
        }

        LocalDateTime baseTime = now.minusHours(24);

        // Distribute metrics into buckets
        for (MetricRecord metric : metrics) {
            long minutesDiff = ChronoUnit.MINUTES.between(baseTime, metric.getMetricTimestamp());
            if (minutesDiff >= 0 && minutesDiff < 1440) {
                minuteBuckets.get((int) minutesDiff).add(metric);
            }
        }

        // Extract 7 features per minute
        for (int minute = 0; minute < 1440; minute++) {
            List<MetricRecord> bucket = minuteBuckets.get(minute);
            Double[] features = new Double[7];

            if (bucket.isEmpty()) {
                Arrays.fill(features, 0.0);
            } else {
                features[0] = calculateAvgResponseTime(bucket);
                features[1] = calculateAvgErrorRate(bucket);
                features[2] = calculateTotalRequests(bucket);
                features[3] = calculateAvgCpuUsage(bucket);
                features[4] = calculateAvgMemoryUsage(bucket);
            }

            // Time features
            LocalDateTime minuteTime = baseTime.plusMinutes(minute);
            features[5] = (double) minuteTime.getHour() / 24.0; // Hour normalized [0, 1]
            features[6] = (double) minuteTime.getDayOfWeek().getValue() / 7.0; // Day normalized

            // Normalize metrics (not time features)
            features = normalizeMetrics(features);
            pleFeatures.add(features);
        }

        return pleFeatures;
    }

    // ==================== Private Helper Methods ====================

    /**
     * Calculate average response time from bucket
     */
    private Double calculateAvgResponseTime(List<MetricRecord> metrics) {
        if (metrics.isEmpty())
            return 0.0;

        return metrics.stream()
                .map(m -> m.getResponseTimeMs() != null ? m.getResponseTimeMs() : 0.0)
                .mapToDouble(Double::doubleValue)
                .average()
                .orElse(0.0);
    }

    /**
     * Calculate average error rate from bucket
     */
    private Double calculateAvgErrorRate(List<MetricRecord> metrics) {
        if (metrics.isEmpty())
            return 0.0;

        return metrics.stream()
                .map(m -> m.getErrorRate() != null ? m.getErrorRate() : 0.0)
                .mapToDouble(Double::doubleValue)
                .average()
                .orElse(0.0);
    }

    /**
     * Calculate total requests from bucket
     */
    private Double calculateTotalRequests(List<MetricRecord> metrics) {
        if (metrics.isEmpty())
            return 0.0;

        return metrics.stream()
                .map(m -> m.getRequestCount() != null ? m.getRequestCount().doubleValue() : 0.0)
                .mapToDouble(Double::doubleValue)
                .sum();
    }

    /**
     * Calculate average CPU usage from bucket
     */
    private Double calculateAvgCpuUsage(List<MetricRecord> metrics) {
        if (metrics.isEmpty())
            return 0.0;

        return metrics.stream()
                .map(m -> m.getCpuUsagePercent() != null ? m.getCpuUsagePercent() : 0.0)
                .mapToDouble(Double::doubleValue)
                .average()
                .orElse(0.0);
    }

    /**
     * Calculate average memory usage from bucket
     */
    private Double calculateAvgMemoryUsage(List<MetricRecord> metrics) {
        if (metrics.isEmpty())
            return 0.0;

        return metrics.stream()
                .map(m -> m.getMemoryUsagePercent() != null ? m.getMemoryUsagePercent() : 0.0)
                .mapToDouble(Double::doubleValue)
                .average()
                .orElse(0.0);
    }

    /**
     * Simple min-max normalization to [0, 1]
     * In production, use pre-computed min/max from training data
     */
    private Double[] normalizeMetrics(Double[] metrics) {
        Double[] normalized = new Double[metrics.length];
        for (int i = 0; i < metrics.length; i++) {
            if (i == 5 || i == 6) {
                // Time features already normalized
                normalized[i] = metrics[i];
            } else {
                // Scale metrics to [0, 1] range
                // Adjust divisor based on your data scale
                double divisor = switch (i) {
                    case 0 -> 1000.0; // responseTimeMs (0-1000ms typical)
                    case 1 -> 1.0; // errorRate (already 0-1)
                    case 2 -> 100.0; // requestCount (0-100 per minute typical)
                    case 3 -> 100.0; // cpuUsage (0-100%)
                    case 4 -> 100.0; // memoryUsage (0-100%)
                    default -> 1000.0;
                };
                normalized[i] = Math.max(0.0, Math.min(1.0, metrics[i] / divisor));
            }
        }
        return normalized;
    }
}
