package com.api.monitoring.backend.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "alert_rules")
public class AlertRecord {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "alert_name", nullable = false)
    private String alertName;

    @Column(name = "alert_description", columnDefinition = "TEXT")
    private String alertDescription;

    @Column(name = "condition_type", nullable = false)
    private String conditionType;

    @Column(name = "condition_expression", nullable = false, columnDefinition = "TEXT")
    private String conditionExpression;

    @Column(name = "threshold_value")
    private Double thresholdValue;

    @Column(name = "severity_level", nullable = false)
    private String severityLevel;

    @Column(name = "is_enabled", nullable = false)
    private Boolean enabled = true;

    @Column(name = "notification_channels", columnDefinition = "jsonb")
    private String notificationChannels;

    @Column(name = "notification_recipients", columnDefinition = "jsonb")
    private String notificationRecipients;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    // Constructors
    public AlertRecord() {
    }

    public AlertRecord(String alertName, String conditionType, String conditionExpression,
            Double thresholdValue, String severityLevel, Boolean enabled,
            String notificationChannels) {
        this.alertName = alertName;
        this.conditionType = conditionType;
        this.conditionExpression = conditionExpression;
        this.thresholdValue = thresholdValue;
        this.severityLevel = severityLevel;
        this.enabled = enabled;
        this.notificationChannels = notificationChannels;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    // Getters and Setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getAlertName() {
        return alertName;
    }

    public void setAlertName(String alertName) {
        this.alertName = alertName;
    }

    public String getAlertDescription() {
        return alertDescription;
    }

    public void setAlertDescription(String alertDescription) {
        this.alertDescription = alertDescription;
    }

    public String getConditionType() {
        return conditionType;
    }

    public void setConditionType(String conditionType) {
        this.conditionType = conditionType;
    }

    public String getConditionExpression() {
        return conditionExpression;
    }

    public void setConditionExpression(String conditionExpression) {
        this.conditionExpression = conditionExpression;
    }

    public Double getThresholdValue() {
        return thresholdValue;
    }

    public void setThresholdValue(Double thresholdValue) {
        this.thresholdValue = thresholdValue;
    }

    public String getSeverityLevel() {
        return severityLevel;
    }

    public void setSeverityLevel(String severityLevel) {
        this.severityLevel = severityLevel;
    }

    public Boolean getEnabled() {
        return enabled;
    }

    public void setEnabled(Boolean enabled) {
        this.enabled = enabled;
    }

    public String getNotificationChannels() {
        return notificationChannels;
    }

    public void setNotificationChannels(String notificationChannels) {
        this.notificationChannels = notificationChannels;
    }

    public String getNotificationRecipients() {
        return notificationRecipients;
    }

    public void setNotificationRecipients(String notificationRecipients) {
        this.notificationRecipients = notificationRecipients;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }

    // Compatibility methods if older code uses them
    public Double getThreshold() {
        return thresholdValue;
    }

    public void setThreshold(Double threshold) {
        this.thresholdValue = threshold;
    }
}
