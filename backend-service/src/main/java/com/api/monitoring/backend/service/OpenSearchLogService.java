package com.api.monitoring.backend.service;

import com.api.monitoring.backend.dto.LogDTO;
import com.api.monitoring.backend.dto.TrafficMetricsDTO;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;
import org.opensearch.action.index.IndexRequest;
import org.opensearch.action.index.IndexResponse;
import org.opensearch.action.search.SearchRequest;
import org.opensearch.action.search.SearchResponse;
import org.opensearch.client.RequestOptions;
import org.opensearch.client.RestHighLevelClient;
import org.opensearch.common.xcontent.XContentType;
import org.opensearch.index.query.QueryBuilders;
import org.opensearch.search.SearchHit;
import org.opensearch.search.builder.SearchSourceBuilder;
import org.opensearch.search.sort.SortOrder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.*;

@Service
public class OpenSearchLogService {

    private static final Logger logger = LoggerFactory.getLogger(OpenSearchLogService.class);
    private static final String INDEX_PREFIX = "api-logs-";
    
    @Autowired(required = false)
    @Qualifier("openSearchClient")
    private RestHighLevelClient openSearchClient;
    
    @Autowired
    private ObjectMapper objectMapper;

    @PostConstruct
    public void init() {
        logger.info("========================================");
        if (openSearchClient != null) {
            logger.info("✓ OpenSearchLogService initialized WITH RestHighLevelClient");
        } else {
            logger.warn("✗ OpenSearchLogService initialized but RestHighLevelClient is NULL!");
        }
        logger.info("========================================");
    }

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

    public TrafficMetricsDTO getTrafficMetrics() {
        TrafficMetricsDTO traffic = new TrafficMetricsDTO();
        traffic.setCurrent(450);
        traffic.setPeak(2000);
        traffic.setAverage(850);
        traffic.setPercentileP95(1500);
        traffic.setTrend("STABLE");
        return traffic;
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

    public String indexLog(LogDTO logDTO) {
        if (openSearchClient == null) {
            logger.warn("⚠ OpenSearch client is NULL - log NOT indexed to OpenSearch");
            return UUID.randomUUID().toString();
        }

        try {
            String logId = UUID.randomUUID().toString();
            logDTO.setLogId(logId);
            
            String indexName = INDEX_PREFIX + 
                LocalDate.now(ZoneOffset.UTC).format(DateTimeFormatter.ofPattern("yyyy.MM.dd"));
            
            Map<String, Object> logMap = new HashMap<>();
            logMap.put("logId", logDTO.getLogId());
            logMap.put("serviceName", logDTO.getServiceName());
            logMap.put("level", logDTO.getLevel());
            logMap.put("message", logDTO.getMessage());
            logMap.put("source", logDTO.getSource());
            logMap.put("timestamp", logDTO.getTimestamp());
            logMap.put("metadata", logDTO.getMetadata());
            logMap.put("traceId", logDTO.getTraceId());
            logMap.put("spanId", logDTO.getSpanId());
            
            String jsonLog = objectMapper.writeValueAsString(logMap);
            
            IndexRequest request = new IndexRequest(indexName)
                .id(logId)
                .source(jsonLog, XContentType.JSON);
            
            IndexResponse response = openSearchClient.index(request, RequestOptions.DEFAULT);
            
            logger.info("✓ Indexed log to OpenSearch: {} in index: {}", logId, indexName);
            return response.getId();
            
        } catch (IOException e) {
            logger.error("✗ Failed to index log to OpenSearch", e);
            return UUID.randomUUID().toString();
        }
    }

    public List<LogDTO> getRecentLogs(int limit) {
        if (openSearchClient == null) {
            logger.warn("⚠ OpenSearch client is NULL - returning empty list");
            return new ArrayList<>();
        }

        try {
            SearchRequest searchRequest = new SearchRequest(INDEX_PREFIX + "*");
            SearchSourceBuilder sourceBuilder = new SearchSourceBuilder();
            sourceBuilder.query(QueryBuilders.matchAllQuery());
            sourceBuilder.sort("timestamp", SortOrder.DESC);
            sourceBuilder.size(limit);
            searchRequest.source(sourceBuilder);
            
            SearchResponse response = openSearchClient.search(searchRequest, RequestOptions.DEFAULT);
            logger.info("✓ Found {} logs in OpenSearch", response.getHits().getTotalHits().value);
            return parseSearchResponse(response);
            
        } catch (IOException e) {
            logger.error("✗ Failed to fetch recent logs from OpenSearch", e);
            return new ArrayList<>();
        }
    }

    public List<LogDTO> searchLogs(String query, int limit) {
        if (openSearchClient == null) {
            return new ArrayList<>();
        }

        try {
            SearchRequest searchRequest = new SearchRequest(INDEX_PREFIX + "*");
            SearchSourceBuilder sourceBuilder = new SearchSourceBuilder();
            sourceBuilder.query(QueryBuilders.queryStringQuery(query));
            sourceBuilder.sort("timestamp", SortOrder.DESC);
            sourceBuilder.size(limit);
            searchRequest.source(sourceBuilder);
            
            SearchResponse response = openSearchClient.search(searchRequest, RequestOptions.DEFAULT);
            return parseSearchResponse(response);
            
        } catch (IOException e) {
            logger.error("Failed to search logs in OpenSearch", e);
            return new ArrayList<>();
        }
    }

    public List<LogDTO> getLogsByService(String serviceName, int limit) {
        if (openSearchClient == null) {
            return new ArrayList<>();
        }

        try {
            SearchRequest searchRequest = new SearchRequest(INDEX_PREFIX + "*");
            SearchSourceBuilder sourceBuilder = new SearchSourceBuilder();
            sourceBuilder.query(QueryBuilders.matchQuery("serviceName", serviceName));
            sourceBuilder.sort("timestamp", SortOrder.DESC);
            sourceBuilder.size(limit);
            searchRequest.source(sourceBuilder);
            
            SearchResponse response = openSearchClient.search(searchRequest, RequestOptions.DEFAULT);
            return parseSearchResponse(response);
            
        } catch (IOException e) {
            logger.error("Failed to fetch logs by service from OpenSearch", e);
            return new ArrayList<>();
        }
    }

    public List<LogDTO> getLogsByLevel(String level, int limit) {
        if (openSearchClient == null) {
            return new ArrayList<>();
        }

        try {
            SearchRequest searchRequest = new SearchRequest(INDEX_PREFIX + "*");
            SearchSourceBuilder sourceBuilder = new SearchSourceBuilder();
            sourceBuilder.query(QueryBuilders.matchQuery("level", level));
            sourceBuilder.sort("timestamp", SortOrder.DESC);
            sourceBuilder.size(limit);
            searchRequest.source(sourceBuilder);
            
            SearchResponse response = openSearchClient.search(searchRequest, RequestOptions.DEFAULT);
            return parseSearchResponse(response);
            
        } catch (IOException e) {
            logger.error("Failed to fetch logs by level from OpenSearch", e);
            return new ArrayList<>();
        }
    }

    private List<LogDTO> parseSearchResponse(SearchResponse response) {
        List<LogDTO> logs = new ArrayList<>();
        
        for (SearchHit hit : response.getHits().getHits()) {
            try {
                Map<String, Object> sourceMap = hit.getSourceAsMap();
                LogDTO log = new LogDTO();
                log.setLogId((String) sourceMap.get("logId"));
                log.setServiceName((String) sourceMap.get("serviceName"));
                log.setLevel((String) sourceMap.get("level"));
                log.setMessage((String) sourceMap.get("message"));
                log.setSource((String) sourceMap.get("source"));
                
                if (sourceMap.get("timestamp") != null) {
                    log.setTimestamp(objectMapper.convertValue(sourceMap.get("timestamp"), java.time.Instant.class));
                }
                
                log.setMetadata((Map<String, Object>) sourceMap.get("metadata"));
                log.setTraceId((String) sourceMap.get("traceId"));
                log.setSpanId((String) sourceMap.get("spanId"));
                
                logs.add(log);
            } catch (Exception e) {
                logger.warn("Failed to parse log from search hit", e);
            }
        }
        
        return logs;
    }
}
