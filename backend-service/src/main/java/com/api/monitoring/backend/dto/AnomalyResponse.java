package com.api.monitoring.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.LocalDateTime;

public class AnomalyResponse {
    private String apiName;
    private Integer stage;
    private String model;
    private Double anomalyScore;
    private Double stage2Score;
    private Double finalAnomalyScore;
    private String status;
    private String severity;
    private Double confidence;
    private String timestamp;
    private Long id;
    private String environment;
    private String serviceName;
    private String endpoint;
    private Double hybridEnsembleScore;
    private String source;

    // Constructors
    public AnomalyResponse() {
    }

    // Getters and Setters
    @JsonProperty("api_name")
    public String getApiName() {
        return apiName;
    }

    @JsonProperty("api_name")
    public void setApiName(String apiName) {
        this.apiName = apiName;
    }

    @JsonProperty("acknowledged")
    private Boolean acknowledged;

    // Note: environment is declared above

    public Integer getStage() {
        return stage;
    }

    public void setStage(Integer stage) {
        this.stage = stage;
    }

    public String getModel() {
        return model;
    }

    public void setModel(String model) {
        this.model = model;
    }

    @JsonProperty("anomaly_score")
    public Double getAnomalyScore() {
        return anomalyScore;
    }

    @JsonProperty("anomaly_score")
    public void setAnomalyScore(Double anomalyScore) {
        this.anomalyScore = anomalyScore;
    }

    @JsonProperty("stage2_score")
    public Double getStage2Score() {
        return stage2Score;
    }

    @JsonProperty("stage2_score")
    public void setStage2Score(Double stage2Score) {
        this.stage2Score = stage2Score;
    }

    @JsonProperty("final_anomaly_score")
    public Double getFinalAnomalyScore() {
        return finalAnomalyScore;
    }

    @JsonProperty("final_anomaly_score")
    public void setFinalAnomalyScore(Double finalAnomalyScore) {
        this.finalAnomalyScore = finalAnomalyScore;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getSeverity() {
        return severity;
    }

    public void setSeverity(String severity) {
        this.severity = severity;
    }

    public Double getConfidence() {
        return confidence;
    }

    public void setConfidence(Double confidence) {
        this.confidence = confidence;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getEnvironment() {
        return environment;
    }

    public void setEnvironment(String environment) {
        this.environment = environment;
    }

    public String getServiceName() {
        return serviceName;
    }

    public void setServiceName(String serviceName) {
        this.serviceName = serviceName;
    }

    public String getEndpoint() {
        return endpoint;
    }

    public void setEndpoint(String endpoint) {
        this.endpoint = endpoint;
    }

    public Double getHybridEnsembleScore() {
        return hybridEnsembleScore;
    }

    public void setHybridEnsembleScore(Double hybridEnsembleScore) {
        this.hybridEnsembleScore = hybridEnsembleScore;
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }
}
