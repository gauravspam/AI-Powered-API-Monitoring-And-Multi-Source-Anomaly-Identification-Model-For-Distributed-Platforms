package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.service.AnomalyService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.util.List;
import java.util.Map;

@RestController
public class AnomalyController {

    private final AnomalyService anomalyService;

    public AnomalyController(AnomalyService anomalyService) {
        this.anomalyService = anomalyService;
    }

    @GetMapping("/api/anomalies")
    public List<Map<String, Object>> getAnomalies() throws IOException {
        List<Map<String, Object>> result = anomalyService.getRecentErrorAnomalies();
        return result == null ? List.of() : result;
    }
}
