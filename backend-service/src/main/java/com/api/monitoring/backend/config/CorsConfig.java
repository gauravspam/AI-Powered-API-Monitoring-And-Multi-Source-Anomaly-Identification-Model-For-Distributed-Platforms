package com.api.monitoring.backend.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.filter.CorsFilter;

@Configuration
public class CorsConfig {

    @Bean
    public CorsFilter corsFilter() {
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        CorsConfiguration config = new CorsConfiguration();

        // ✅ Allow Credentials (Cookies/Auth)
        config.setAllowCredentials(true);

        // ✅ Add Vite Dev Server
        config.addAllowedOrigin("http://localhost:5173");

        // Keep existing
        config.addAllowedOrigin("http://localhost:3000");
        config.addAllowedOrigin("http://localhost:8082");

        config.addAllowedHeader("*");
        config.addAllowedMethod("*"); // Allow all methods (GET, POST, etc.)

        config.setMaxAge(3600L);
        source.registerCorsConfiguration("/**", config);
        return new CorsFilter(source);
    }
}
