package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.service.OverviewService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.util.List;
import java.util.Map;

@RestController
public class OverviewController {

    private final OverviewService overviewService;

    public OverviewController(OverviewService overviewService) {
        this.overviewService = overviewService;
    }

    @GetMapping("/api/overview")
    public Map<String, Object> getOverview() throws IOException {
        return overviewService.getOverview();
    }

    @GetMapping("/api/overview/environment-summary")
    public List<Map<String, Object>> getEnvironmentSummary() {
        return overviewService.getEnvironmentSummary();
    }
}
