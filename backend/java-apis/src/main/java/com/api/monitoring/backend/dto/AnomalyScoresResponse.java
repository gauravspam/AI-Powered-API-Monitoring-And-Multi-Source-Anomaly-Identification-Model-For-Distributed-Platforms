package com.api.monitoring.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;

/**
 * NEW: Response DTO for time-series feature-based predictions
 * Complements existing AnomalyResponse (which is for single log entries)
 * This is for MSIF-LSTM + PLE-GRU predictions on feature windows
 */
public class AnomalyScoresResponse {

    @JsonProperty("msif_lstm_score")
    private Double msifLstmScore;

    @JsonProperty("ple_gru_score")
    private Double pleGruScore;

    @JsonProperty("ple_probability_dist")
    private Map<String, Double> pleProbabilityDist;

    @JsonProperty("hybrid_score")
    private Double hybridScore;

    private Double confidence;

    @JsonProperty("weights_used")
    private Map<String, Double> weightsUsed;

    @JsonProperty("fusion_method")
    private String fusionMethod;

    private String context;

    private Long processingTimeMs;

    @JsonProperty("model_versions")
    private Map<String, String> modelVersions;

    // Constructors
    public AnomalyScoresResponse() {
    }

    public AnomalyScoresResponse(
            Double msifLstmScore,
            Double pleGruScore,
            Map<String, Double> pleProbabilityDist,
            Double hybridScore,
            Double confidence,
            Map<String, Double> weightsUsed,
            String fusionMethod) {
        this.msifLstmScore = msifLstmScore;
        this.pleGruScore = pleGruScore;
        this.pleProbabilityDist = pleProbabilityDist;
        this.hybridScore = hybridScore;
        this.confidence = confidence;
        this.weightsUsed = weightsUsed;
        this.fusionMethod = fusionMethod;
    }

    // Getters & Setters
    public Double getMsifLstmScore() {
        return msifLstmScore;
    }

    public void setMsifLstmScore(Double msifLstmScore) {
        this.msifLstmScore = msifLstmScore;
    }

    public Double getPleGruScore() {
        return pleGruScore;
    }

    public void setPleGruScore(Double pleGruScore) {
        this.pleGruScore = pleGruScore;
    }

    public Map<String, Double> getPleProbabilityDist() {
        return pleProbabilityDist;
    }

    public void setPleProbabilityDist(Map<String, Double> pleProbabilityDist) {
        this.pleProbabilityDist = pleProbabilityDist;
    }

    public Double getHybridScore() {
        return hybridScore;
    }

    public void setHybridScore(Double hybridScore) {
        this.hybridScore = hybridScore;
    }

    public Double getConfidence() {
        return confidence;
    }

    public void setConfidence(Double confidence) {
        this.confidence = confidence;
    }

    public Map<String, Double> getWeightsUsed() {
        return weightsUsed;
    }

    public void setWeightsUsed(Map<String, Double> weightsUsed) {
        this.weightsUsed = weightsUsed;
    }

    public String getFusionMethod() {
        return fusionMethod;
    }

    public void setFusionMethod(String fusionMethod) {
        this.fusionMethod = fusionMethod;
    }

    public String getContext() {
        return context;
    }

    public void setContext(String context) {
        this.context = context;
    }

    public Long getProcessingTimeMs() {
        return processingTimeMs;
    }

    public void setProcessingTimeMs(Long processingTimeMs) {
        this.processingTimeMs = processingTimeMs;
    }

    public Map<String, String> getModelVersions() {
        return modelVersions;
    }

    public void setModelVersions(Map<String, String> modelVersions) {
        this.modelVersions = modelVersions;
    }
}
