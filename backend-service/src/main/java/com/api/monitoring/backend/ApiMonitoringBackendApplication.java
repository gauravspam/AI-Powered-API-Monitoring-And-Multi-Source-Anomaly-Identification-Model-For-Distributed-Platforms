package com.api.monitoring.backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class ApiMonitoringBackendApplication {

    public static void main(String[] args) {
        SpringApplication.run(ApiMonitoringBackendApplication.class, args);
    }
}
