package com.api.monitoring.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class ModelInfoResponse {
    @JsonProperty("stage1_model")
    private String stage1Model;
    
    @JsonProperty("stage2_model")
    private String stage2Model;
    
    @JsonProperty("confidence_threshold_stage1")
    private Double confidenceThresholdStage1;
    
    @JsonProperty("confidence_threshold_stage2")
    private Double confidenceThresholdStage2;
    
    private Integer features;
    private String description;

    // Constructors
    public ModelInfoResponse() {}

    // Getters and Setters
    public String getStage1Model() {
        return stage1Model;
    }

    public void setStage1Model(String stage1Model) {
        this.stage1Model = stage1Model;
    }

    public String getStage2Model() {
        return stage2Model;
    }

    public void setStage2Model(String stage2Model) {
        this.stage2Model = stage2Model;
    }

    public Double getConfidenceThresholdStage1() {
        return confidenceThresholdStage1;
    }

    public void setConfidenceThresholdStage1(Double confidenceThresholdStage1) {
        this.confidenceThresholdStage1 = confidenceThresholdStage1;
    }

    public Double getConfidenceThresholdStage2() {
        return confidenceThresholdStage2;
    }

    public void setConfidenceThresholdStage2(Double confidenceThresholdStage2) {
        this.confidenceThresholdStage2 = confidenceThresholdStage2;
    }

    public Integer getFeatures() {
        return features;
    }

    public void setFeatures(Integer features) {
        this.features = features;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }
}

