package com.api.monitoring.backend.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LogEntryRequest {

    // Allow mapping from "apiName" or "serviceName" in JSON
    @JsonAlias({ "apiName", "serviceName" })
    private String serviceName;

    private String endpoint;

    @JsonAlias({ "method", "httpMethod" })
    private String httpMethod;

    private Integer statusCode;
    private Long responseTime;
    private Long requestSizeBytes;
    private Long responseSizeBytes;

    // Metrics
    private Integer requestCount;
    private Double errorRate;
    private Double cpuUsage;
    private Double memoryUsage;
    private Double networkIo;
    private Double diskIo;

    // Context
    private Integer hourOfDay;
    private Integer dayOfWeek;
    private String timestamp;
    private String traceId;

    // Compatibility getters for legacy code
    public String getApiName() {
        return serviceName;
    }

    public void setApiName(String apiName) {
        this.serviceName = apiName;
    }

    public String getMethod() {
        return httpMethod;
    }

    public void setMethod(String method) {
        this.httpMethod = method;
    }
}
