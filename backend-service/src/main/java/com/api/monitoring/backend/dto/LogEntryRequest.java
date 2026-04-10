package com.api.monitoring.backend.dto;

import java.time.LocalDateTime;

public class LogEntryRequest {
    private String apiName;
    private String method;
    private Double responseTime;
    private Integer statusCode;
    private Integer requestCount;
    private Double errorRate;
    private Double cpuUsage;
    private Double memoryUsage;
    private Double networkIo;
    private Double diskIo;
    private Integer hourOfDay;
    private Integer dayOfWeek;
    private String timestamp;
    private String environment = "production";
    private String serviceName = "api-monitoring";

    // Constructors
    public LogEntryRequest() {
    }

    // Getters and Setters (plain, no @JsonProperty)
    public String getApiName() {
        return apiName;
    }

    public void setApiName(String apiName) {
        this.apiName = apiName;
    }

    public String getMethod() {
        return method;
    }

    public void setMethod(String method) {
        this.method = method;
    }

    public Double getResponseTime() {
        return responseTime;
    }

    public void setResponseTime(Double responseTime) {
        this.responseTime = responseTime;
    }

    public Integer getStatusCode() {
        return statusCode;
    }

    public void setStatusCode(Integer statusCode) {
        this.statusCode = statusCode;
    }

    public Integer getRequestCount() {
        return requestCount;
    }

    public void setRequestCount(Integer requestCount) {
        this.requestCount = requestCount;
    }

    public Double getErrorRate() {
        return errorRate;
    }

    public void setErrorRate(Double errorRate) {
        this.errorRate = errorRate;
    }

    public Double getCpuUsage() {
        return cpuUsage;
    }

    public void setCpuUsage(Double cpuUsage) {
        this.cpuUsage = cpuUsage;
    }

    public Double getMemoryUsage() {
        return memoryUsage;
    }

    public void setMemoryUsage(Double memoryUsage) {
        this.memoryUsage = memoryUsage;
    }

    public Double getNetworkIo() {
        return networkIo;
    }

    public void setNetworkIo(Double networkIo) {
        this.networkIo = networkIo;
    }

    public Double getDiskIo() {
        return diskIo;
    }

    public void setDiskIo(Double diskIo) {
        this.diskIo = diskIo;
    }

    public Integer getHourOfDay() {
        return hourOfDay;
    }

    public void setHourOfDay(Integer hourOfDay) {
        this.hourOfDay = hourOfDay;
    }

    public Integer getDayOfWeek() {
        return dayOfWeek;
    }

    public void setDayOfWeek(Integer dayOfWeek) {
        this.dayOfWeek = dayOfWeek;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }

    public String getEnvironment() {
        return environment;
    }

    public void setEnvironment(String environment) {
        this.environment = environment;
    }

    public String getServiceName() {
        return serviceName;
    }

    public void setServiceName(String serviceName) {
        this.serviceName = serviceName;
    }
}
