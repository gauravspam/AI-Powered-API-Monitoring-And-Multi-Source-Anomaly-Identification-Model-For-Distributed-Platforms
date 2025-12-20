package com.api.monitoring.backend.service;

import org.opensearch.action.search.SearchRequest;
import org.opensearch.action.search.SearchResponse;
import org.opensearch.client.RequestOptions;
import org.opensearch.client.RestHighLevelClient;
import org.opensearch.index.query.QueryBuilders;
import org.opensearch.search.aggregations.AggregationBuilders;
import org.opensearch.search.aggregations.bucket.terms.Terms;
import org.opensearch.search.aggregations.metrics.Max;
import org.opensearch.search.builder.SearchSourceBuilder;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.List;
import java.util.Map;

@Service
public class OverviewService {

    private final RestHighLevelClient client;

    public OverviewService(RestHighLevelClient client) {
        this.client = client;
    }

    public Map<String, Object> getOverview() throws IOException {
        SearchRequest request = new SearchRequest("api-logs-test*"); // later: api-logs-*
        SearchSourceBuilder sourceBuilder = new SearchSourceBuilder()
                .query(QueryBuilders.matchAllQuery())
                .size(0) // we only want aggregations
                .aggregation(AggregationBuilders.terms("by_service").field("service.keyword"))
                .aggregation(AggregationBuilders.max("last_ts").field("timestamp"));

        request.source(sourceBuilder);

        SearchResponse response = client.search(request, RequestOptions.DEFAULT);

        long totalLogs = response.getHits().getTotalHits().value;

        Terms byService = response.getAggregations().get("by_service");
        List<Map<String, Object>> services = byService.getBuckets().stream()
                .map(b -> Map.<String, Object>of(
                        "name", b.getKeyAsString(),
                        "count", b.getDocCount()
                ))
                .toList();

        Max lastTs = response.getAggregations().get("last_ts");
        double lastTimestamp = lastTs.getValue(); // can be NaN if no docs

        return Map.of(
                "totalLogs", totalLogs,
                "services", services,
                "lastLogTimestamp", Double.isNaN(lastTimestamp) ? null : (long) lastTimestamp
        );
    }
}
