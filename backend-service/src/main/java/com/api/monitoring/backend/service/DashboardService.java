package com.api.monitoring.backend.service;

import com.api.monitoring.backend.service.OpenSearchLogService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class DashboardService {

    @Autowired
    private OpenSearchLogService logService;

    public long getTotalRequests() {
        return 10000L;
    }

    public double getSuccessRate() {
        return 97.5;
    }

    public double getErrorRate() {
        return 2.5;
    }

    public double getAvgLatency() {
        return 120.0;
    }

    public double getP95Latency() {
        return 250.0;
    }

    public double getP99Latency() {
        return 450.0;
    }

    public int getCurrentRPS() {
        return 450;
    }

    public int getPeakRPS() {
        return 2000;
    }

    public int getAverageRPS() {
        return 850;
    }

    public int getActiveServices() {
        return 5;
    }

    public int getAnomalyCount() {
        return 3;
    }

    public int getAlertCount() {
        return 0;
    }
}