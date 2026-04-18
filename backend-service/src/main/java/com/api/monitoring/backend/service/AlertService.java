package com.api.monitoring.backend.service;

import com.api.monitoring.backend.model.AlertRecord;
import com.api.monitoring.backend.model.AnomalyRecord;
import com.api.monitoring.backend.repository.AlertRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.*;

@Service
@Slf4j
public class AlertService {

    private final AlertRepository alertRepository;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    @Value("${alert.teams.webhook:}")
    private String teamsWebhookUrl;

    @Value("${alert.slack.webhook:}")
    private String slackWebhookUrl;

    @Value("${alert.email.enabled:false}")
    private boolean emailEnabled;

    @Value("${alert.email.smtp-host:}")
    private String smtpHost;

    @Value("${alert.email.smtp-port:587}")
    private int smtpPort;

    @Value("${alert.email.from:}")
    private String emailFrom;

    @Value("${alert.email.to:}")
    private String emailTo;

    @Value("${alert.pagerduty.enabled:false}")
    private boolean pagerdutyEnabled;

    @Value("${alert.pagerduty.api-key:}")
    private String pagerdutyApiKey;

    @Value("${alert.pagerduty.service-id:}")
    private String pagerdutyServiceId;

    @Autowired
    public AlertService(AlertRepository alertRepository) {
        this.alertRepository = alertRepository;
        this.restTemplate = new RestTemplate();
        this.objectMapper = new ObjectMapper();
    }

    @Async
    public void triggerAlert(AnomalyRecord anomaly) {
        log.info("Triggering alert for anomaly: {}, score: {}", anomaly.getId(), anomaly.getAnomalyScore());

        List<AlertRecord> activeRules = alertRepository.findByEnabledTrue();

        for (AlertRecord rule : activeRules) {
            if (evaluateRule(rule, anomaly)) {
                sendNotifications(rule, anomaly);
            }
        }
    }

    public void triggerAlertForRule(AlertRecord rule, AnomalyRecord anomaly) {
        if (evaluateRule(rule, anomaly)) {
            sendNotifications(rule, anomaly);
        }
    }

    private boolean evaluateRule(AlertRecord rule, AnomalyRecord anomaly) {
        double score = anomaly.getAnomalyScore();
        Double threshold = rule.getThresholdValue();

        if (threshold == null) {
            return false;
        }

        return switch (rule.getConditionType()) {
            case "ABOVE" -> score > threshold;
            case "BELOW" -> score < threshold;
            case "EQUALS" -> Math.abs(score - threshold) < 0.01;
            default -> false;
        };
    }

    private void sendNotifications(AlertRecord rule, AnomalyRecord anomaly) {
        try {
            String channelsJson = rule.getNotificationChannels();
            List<String> channels = Arrays.asList(objectMapper.readValue(channelsJson, String[].class));

            for (String channel : channels) {
                switch (channel.toLowerCase()) {
                    case "teams" -> sendTeamsNotification(rule, anomaly);
                    case "slack" -> sendSlackNotification(rule, anomaly);
                    case "email" -> sendEmailNotification(rule, anomaly);
                    case "pagerduty" -> sendPagerDutyNotification(rule, anomaly);
                    default -> log.warn("Unknown notification channel: {}", channel);
                }
            }
        } catch (Exception e) {
            log.error("Failed to send notifications: {}", e.getMessage(), e);
        }
    }

    private void sendTeamsNotification(AlertRecord rule, AnomalyRecord anomaly) {
        if (teamsWebhookUrl == null || teamsWebhookUrl.isBlank()) {
            log.warn("Teams webhook not configured");
            return;
        }

        try {
            Map<String, Object> payload = new HashMap<>();
            payload.put("@type", "MessageCard");
            payload.put("@context", "http://schema.org/extensions");
            payload.put("themeColor", getSeverityColor(anomaly.getSeverity()));
            payload.put("summary", "Alert: " + rule.getAlertName());

            Map<String, Object> section = new HashMap<>();
            section.put("activityTitle", "🚨 " + rule.getAlertName());
            section.put("facts", Arrays.asList(
                    Map.of("name", "Severity", "value", anomaly.getSeverity() != null ? anomaly.getSeverity() : "HIGH"),
                    Map.of("name", "Anomaly Score", "value", String.format("%.4f", anomaly.getAnomalyScore())),
                    Map.of("name", "Endpoint", "value", anomaly.getEndpoint() != null ? anomaly.getEndpoint() : "N/A"),
                    Map.of("name", "Time", "value", anomaly.getCreatedAt().toString())
            ));
            section.put("markdown", true);

            payload.put("sections", Collections.singletonList(section));

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(payload, headers);

            restTemplate.postForEntity(teamsWebhookUrl, request, String.class);
            log.info("Teams notification sent for anomaly: {}", anomaly.getId());
        } catch (Exception e) {
            log.error("Failed to send Teams notification: {}", e.getMessage());
        }
    }

    private void sendSlackNotification(AlertRecord rule, AnomalyRecord anomaly) {
        if (slackWebhookUrl == null || slackWebhookUrl.isBlank()) {
            log.warn("Slack webhook not configured");
            return;
        }

        try {
            Map<String, Object> payload = new HashMap<>();
            payload.put("text", "🚨 *" + rule.getAlertName() + "*");

            Map<String, Object> attachments = new HashMap<>();
            attachments.put("color", getSeverityColor(anomaly.getSeverity()));
            attachments.put("fields", Arrays.asList(
                    Map.of("title", "Severity", "value", anomaly.getSeverity() != null ? anomaly.getSeverity() : "HIGH", "short", true),
                    Map.of("title", "Score", "value", String.format("%.4f", anomaly.getAnomalyScore()), "short", true),
                    Map.of("title", "Endpoint", "value", anomaly.getEndpoint() != null ? anomaly.getEndpoint() : "N/A", "short", true)
            ));

            payload.put("attachments", Collections.singletonList(attachments));

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(payload, headers);

            restTemplate.postForEntity(slackWebhookUrl, request, String.class);
            log.info("Slack notification sent for anomaly: {}", anomaly.getId());
        } catch (Exception e) {
            log.error("Failed to send Slack notification: {}", e.getMessage());
        }
    }

    private void sendEmailNotification(AlertRecord rule, AnomalyRecord anomaly) {
        if (!emailEnabled || emailFrom.isBlank() || emailTo.isBlank()) {
            log.warn("Email notification not configured");
            return;
        }

        log.info("Email notification would be sent to: {} (SMTP: {}:{})", emailTo, smtpHost, smtpPort);
        log.info("Email content: Alert {} - Score: {}", rule.getAlertName(), anomaly.getAnomalyScore());
    }

    private void sendPagerDutyNotification(AlertRecord rule, AnomalyRecord anomaly) {
        if (!pagerdutyEnabled || pagerdutyApiKey.isBlank() || pagerdutyServiceId.isBlank()) {
            log.warn("PagerDuty not configured");
            return;
        }

        try {
            Map<String, Object> payload = new HashMap<>();
            payload.put("routing_key", pagerdutyServiceId);
            payload.put("event_action", "trigger");
            payload.put("dedup_key", "anomaly-" + anomaly.getId());
            payload.put("payload", Map.of(
                    "summary", rule.getAlertName() + " - Score: " + String.format("%.4f", anomaly.getAnomalyScore()),
                    "severity", mapSeverityToPagerDuty(anomaly.getSeverity()),
                    "source", "api-monitoring-backend",
                    "custom_details", Map.of(
                            "anomaly_id", anomaly.getId(),
                            "score", anomaly.getAnomalyScore(),
                            "endpoint", anomaly.getEndpoint() != null ? anomaly.getEndpoint() : "N/A",
                            "created_at", anomaly.getCreatedAt().toString()
                    )
            ));

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("Authorization", "Token token=" + pagerdutyApiKey);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(payload, headers);

            String url = "https://events.pagerduty.com/v2/enqueue";
            restTemplate.postForEntity(url, request, String.class);
            log.info("PagerDuty notification sent for anomaly: {}", anomaly.getId());
        } catch (Exception e) {
            log.error("Failed to send PagerDuty notification: {}", e.getMessage());
        }
    }

    private String getSeverityColor(String severity) {
        if (severity == null) return "ff0000";
        return switch (severity.toUpperCase()) {
            case "CRITICAL" -> "ff0000";
            case "HIGH" -> "ff6600";
            case "MEDIUM" -> "ffcc00";
            case "LOW" -> "00cc00";
            default -> "cccccc";
        };
    }

    private String mapSeverityToPagerDuty(String severity) {
        if (severity == null) return "warning";
        return switch (severity.toUpperCase()) {
            case "CRITICAL" -> "critical";
            case "HIGH" -> "error";
            case "MEDIUM" -> "warning";
            default -> "info";
        };
    }
}