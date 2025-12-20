package com.api.monitoring.backend.service;

import org.opensearch.action.search.SearchRequest;
import org.opensearch.action.search.SearchResponse;
import org.opensearch.client.RequestOptions;
import org.opensearch.client.RestHighLevelClient;
import org.opensearch.index.query.BoolQueryBuilder;
import org.opensearch.index.query.QueryBuilders;
import org.opensearch.search.builder.SearchSourceBuilder;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

@Service
public class AnomalyService {

    private final RestHighLevelClient client;

    public AnomalyService(RestHighLevelClient client) {
        this.client = client;
    }

    public List<Map<String, Object>> getRecentErrorAnomalies() throws IOException {
        long now = System.currentTimeMillis();
        long fifteenMinutesAgo = now - 15 * 60 * 1000L;

        BoolQueryBuilder bool = QueryBuilders.boolQuery()
                .filter(QueryBuilders.termQuery("level.keyword", "ERROR"))
                .filter(QueryBuilders.rangeQuery("timestamp")
                        .gte(fifteenMinutesAgo)
                        .lte(now));

        SearchSourceBuilder source = new SearchSourceBuilder()
                .query(bool)
                .size(100)
                .sort("timestamp");

        SearchRequest request = new SearchRequest("api-logs-test*").source(source);

        SearchResponse response = client.search(request, RequestOptions.DEFAULT);

        return Arrays.stream(response.getHits().getHits())
                .map(hit -> hit.getSourceAsMap())
                .toList();
    }
}
