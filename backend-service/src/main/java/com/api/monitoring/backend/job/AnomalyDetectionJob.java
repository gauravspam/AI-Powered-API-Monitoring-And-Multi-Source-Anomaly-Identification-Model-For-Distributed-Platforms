package com.api.monitoring.backend.job;

import com.api.monitoring.backend.service.AnomalyService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

@Component
public class AnomalyDetectionJob {

    private static final Logger logger = LoggerFactory.getLogger(AnomalyDetectionJob.class);

    @Autowired
    private AnomalyService anomalyService;

    private int successCount = 0;
    private int failureCount = 0;
    private LocalDateTime lastExecutionTime;
    private String status = "IDLE";

    /**
     * Scheduled job: runs every 5 minutes
     */
    @Scheduled(fixedRate = 300000) // 5 minutes = 300,000 ms
    public void detectAnomalies() {
        logger.info("Starting scheduled anomaly detection job...");
        status = "RUNNING";
        
        try {
            // Call anomaly service to process all APIs
            anomalyService.detectAndSaveAnomalies();
            
            successCount++;
            status = "SUCCESS";
            lastExecutionTime = LocalDateTime.now();
            
            logger.info("Anomaly detection job completed successfully");
            
        } catch (Exception e) {
            failureCount++;
            status = "FAILED";
            lastExecutionTime = LocalDateTime.now();
            
            logger.error("Anomaly detection job failed: {}", e.getMessage(), e);
        }
    }

    // Getters for AdminController
    public int getSuccessCount() {
        return successCount;
    }

    public int getFailureCount() {
        return failureCount;
    }

    public LocalDateTime getLastExecutionTime() {
        return lastExecutionTime;
    }

    public String getStatus() {
        return status;
    }
}
