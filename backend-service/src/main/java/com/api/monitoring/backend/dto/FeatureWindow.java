package com.api.monitoring.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * NEW: Feature window for time-series based anomaly detection
 * Contains aggregated metrics over time windows for MSIF-LSTM and PLE-GRU
 */
public class FeatureWindow {

    private String endpoint;
    private String method;

    @JsonProperty("msif_features")
    private List<Double[]> msifFeatures; // [60 timesteps][5 metrics]

    @JsonProperty("ple_features")
    private List<Double[]> pleFeatures; // [1440 timesteps][5 metrics + 2 time features]

    private Integer windowSizeMins;

    @JsonProperty("start_timestamp")
    private Long startTimestamp;

    @JsonProperty("end_timestamp")
    private Long endTimestamp;

    // Constructors
    public FeatureWindow() {
    }

    public FeatureWindow(
            String endpoint,
            String method,
            List<Double[]> msifFeatures,
            List<Double[]> pleFeatures,
            Integer windowSizeMins) {
        this.endpoint = endpoint;
        this.method = method;
        this.msifFeatures = msifFeatures;
        this.pleFeatures = pleFeatures;
        this.windowSizeMins = windowSizeMins;
    }

    // Getters & Setters
    public String getEndpoint() {
        return endpoint;
    }

    public void setEndpoint(String endpoint) {
        this.endpoint = endpoint;
    }

    public String getMethod() {
        return method;
    }

    public void setMethod(String method) {
        this.method = method;
    }

    public List<Double[]> getMsifFeatures() {
        return msifFeatures;
    }

    public void setMsifFeatures(List<Double[]> msifFeatures) {
        this.msifFeatures = msifFeatures;
    }

    public List<Double[]> getPleFeatures() {
        return pleFeatures;
    }

    public void setPleFeatures(List<Double[]> pleFeatures) {
        this.pleFeatures = pleFeatures;
    }

    public Integer getWindowSizeMins() {
        return windowSizeMins;
    }

    public void setWindowSizeMins(Integer windowSizeMins) {
        this.windowSizeMins = windowSizeMins;
    }

    public Long getStartTimestamp() {
        return startTimestamp;
    }

    public void setStartTimestamp(Long startTimestamp) {
        this.startTimestamp = startTimestamp;
    }

    public Long getEndTimestamp() {
        return endTimestamp;
    }

    public void setEndTimestamp(Long endTimestamp) {
        this.endTimestamp = endTimestamp;
    }
}
