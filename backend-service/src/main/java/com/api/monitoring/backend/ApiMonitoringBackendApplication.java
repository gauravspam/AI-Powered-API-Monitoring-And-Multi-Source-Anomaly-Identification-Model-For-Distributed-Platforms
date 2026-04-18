package com.api.monitoring.backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.retry.annotation.EnableRetry;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Main Application Class for API Monitoring Backend
 *
 * Priority 1 Annotations:
 * - @EnableRetry: Enables retry mechanism for ML service calls
 * - @EnableCaching: Enables caching for ML service health checks
 * - @EnableScheduling: Enables scheduled jobs (for Priority 2)
 * - @EnableAsync: Enables async notification sending
 */
@SpringBootApplication
@EnableRetry
@EnableCaching
@EnableScheduling
@EnableAsync
public class ApiMonitoringBackendApplication {

    public static void main(String[] args) {
        SpringApplication.run(ApiMonitoringBackendApplication.class, args);

        System.out.println(
            "\n" +
                "╔═══════════════════════════════════════════════════════════╗\n" +
                "║   🚀 API Monitoring Backend Service Started              ║\n" +
                "║   📊 Priority 1: ML Integration Active                   ║\n" +
                "║   🔗 Swagger UI: http://localhost:8080/swagger-ui.html   ║\n" +
                "║   💚 Health Check: http://localhost:8080/actuator/health ║\n" +
                "╚═══════════════════════════════════════════════════════════╝\n"
        );
    }
}
