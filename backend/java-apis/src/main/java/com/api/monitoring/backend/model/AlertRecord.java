package main.java.com.api.monitoring.backend.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "alerts")
public class AlertRecord {
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private UUID id;

    @Column(name = "alert_name", nullable = false)
    private String alertName;

    @Column(nullable = false)
    private String condition;

    @Column(nullable = false, precision = 10, scale = 2)
    private Double threshold;

    @Column(nullable = false)
    private Boolean enabled;

    @Column(name = "notification_channels", columnDefinition = "jsonb")
    private String notificationChannels;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    // Constructors
    public AlertRecord() {
    }

    public AlertRecord(String alertName, String condition, Double threshold, Boolean enabled, String notificationChannels) {
        this.alertName = alertName;
        this.condition = condition;
        this.threshold = threshold;
        this.enabled = enabled;
        this.notificationChannels = notificationChannels;
        this.createdAt = LocalDateTime.now();
    }

    // Getters and Setters
    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
    }

    public String getAlertName() {
        return alertName;
    }

    public void setAlertName(String alertName) {
        this.alertName = alertName;
    }

    public String getCondition() {
        return condition;
    }

    public void setCondition(String condition) {
        this.condition = condition;
    }

    public Double getThreshold() {
        return threshold;
    }

    public void setThreshold(Double threshold) {
        this.threshold = threshold;
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
}