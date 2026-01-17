package com.api.monitoring.backend;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.Map;

@RestController
public class ApiController {

    @GetMapping("/")
    public Map<String, String> home() {
        return Map.of("message", "API Monitoring Backend is running");
    }

    // @GetMapping("/api/health")
    // public String health() {
    //     return "OK";
    // }
}