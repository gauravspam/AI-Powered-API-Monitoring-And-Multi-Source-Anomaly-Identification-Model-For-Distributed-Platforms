package com.api.monitoring.backend.controller;

import com.api.monitoring.backend.dto.AnomalyResponse;
import com.api.monitoring.backend.service.AnomalyService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/alerts")
@CrossOrigin(origins = "*")
public class AlertsController {

    @Autowired
    private AnomalyService anomalyService;

    @GetMapping
    public ResponseEntity<List<AnomalyResponse>> getAlerts(
            @RequestParam(defaultValue = "50") int limit) {
        try {
            List<AnomalyResponse> anomalies = anomalyService.getRecentAnomalies(limit);
            return ResponseEntity.ok(anomalies);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @PostMapping("/{id}/acknowledge")
    public ResponseEntity<Boolean> acknowledgeAlert(@PathVariable Long id) {
        try {
            boolean success = anomalyService.acknowledgeAnomaly(id);
            return ResponseEntity.ok(success);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @PostMapping("/{id}/resolve")
    public ResponseEntity<Boolean> resolveAlert(@PathVariable Long id) {
        try {
            boolean success = anomalyService.resolveAnomaly(id);
            return ResponseEntity.ok(success);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}