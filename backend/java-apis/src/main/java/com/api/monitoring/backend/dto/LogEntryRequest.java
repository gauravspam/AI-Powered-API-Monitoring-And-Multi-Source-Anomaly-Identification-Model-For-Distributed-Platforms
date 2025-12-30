package com.api.monitoring.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.LocalDateTime;

public class LogEntryRequest {
    private String apiName;
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

    // Constructors
    public LogEntryRequest() {}

    // Getters and Setters
    @JsonProperty("api_name")
    public String getApiName() {
        return apiName;
    }

    @JsonProperty("api_name")
    public void setApiName(String apiName) {
        this.apiName = apiName;
    }

    @JsonProperty("response_time")
    public Double getResponseTime() {
        return responseTime;
    }

    @JsonProperty("response_time")
    public void setResponseTime(Double responseTime) {
        this.responseTime = responseTime;
    }

    @JsonProperty("status_code")
    public Integer getStatusCode() {
        return statusCode;
    }

    @JsonProperty("status_code")
    public void setStatusCode(Integer statusCode) {
        this.statusCode = statusCode;
    }

    @JsonProperty("request_count")
    public Integer getRequestCount() {
        return requestCount;
    }

    @JsonProperty("request_count")
    public void setRequestCount(Integer requestCount) {
        this.requestCount = requestCount;
    }

    @JsonProperty("error_rate")
    public Double getErrorRate() {
        return errorRate;
    }

    @JsonProperty("error_rate")
    public void setErrorRate(Double errorRate) {
        this.errorRate = errorRate;
    }

    @JsonProperty("cpu_usage")
    public Double getCpuUsage() {
        return cpuUsage;
    }

    @JsonProperty("cpu_usage")
    public void setCpuUsage(Double cpuUsage) {
        this.cpuUsage = cpuUsage;
    }

    @JsonProperty("memory_usage")
    public Double getMemoryUsage() {
        return memoryUsage;
    }

    @JsonProperty("memory_usage")
    public void setMemoryUsage(Double memoryUsage) {
        this.memoryUsage = memoryUsage;
    }

    @JsonProperty("network_io")
    public Double getNetworkIo() {
        return networkIo;
    }

    @JsonProperty("network_io")
    public void setNetworkIo(Double networkIo) {
        this.networkIo = networkIo;
    }

    @JsonProperty("disk_io")
    public Double getDiskIo() {
        return diskIo;
    }

    @JsonProperty("disk_io")
    public void setDiskIo(Double diskIo) {
        this.diskIo = diskIo;
    }

    @JsonProperty("hour_of_day")
    public Integer getHourOfDay() {
        return hourOfDay;
    }

    @JsonProperty("hour_of_day")
    public void setHourOfDay(Integer hourOfDay) {
        this.hourOfDay = hourOfDay;
    }

    @JsonProperty("day_of_week")
    public Integer getDayOfWeek() {
        return dayOfWeek;
    }

    @JsonProperty("day_of_week")
    public void setDayOfWeek(Integer dayOfWeek) {
        this.dayOfWeek = dayOfWeek;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }
}

