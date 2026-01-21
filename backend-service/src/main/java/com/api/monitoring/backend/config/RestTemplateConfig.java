package com.api.monitoring.backend.config;

import java.time.Duration;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.retry.annotation.EnableRetry;
import org.springframework.web.client.RestTemplate;

/**
 * Configuration for RestTemplate beans
 * Used by MLServiceClient to call Python ML service
 */
@Configuration
@EnableRetry
public class RestTemplateConfig {

    /**
     * Main RestTemplate bean for ML service calls
     * Configured with appropriate timeouts
     */
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder
            .setConnectTimeout(Duration.ofSeconds(5))
            .setReadTimeout(Duration.ofSeconds(30))
            .build();
    }

    /**
     * Lightweight RestTemplate for health checks
     * Shorter timeouts for quick health verification
     */
    @Bean(name = "healthCheckRestTemplate")
    public RestTemplate healthCheckRestTemplate() {
        SimpleClientHttpRequestFactory factory =
            new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofSeconds(2));
        factory.setReadTimeout(Duration.ofSeconds(5));

        return new RestTemplate(factory);
    }
}
