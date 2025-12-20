package com.api.monitoring.backend.service;

import org.opensearch.action.index.IndexRequest;
import org.opensearch.action.search.SearchRequest;
import org.opensearch.action.search.SearchResponse;
import org.opensearch.client.RequestOptions;
import org.opensearch.client.RestHighLevelClient;
import org.opensearch.index.query.QueryBuilders;
import org.opensearch.search.builder.SearchSourceBuilder;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.Map;

@Service
public class OpenSearchLogService {

    private final RestHighLevelClient client;

    public OpenSearchLogService(RestHighLevelClient client) {
        this.client = client;
    }

    public void indexTestLog(Map<String, Object> doc) throws IOException {
        IndexRequest request = new IndexRequest("api-logs-test")
                .source(doc);
        client.index(request, RequestOptions.DEFAULT);
    }

    public SearchResponse findAllTestLogs() throws IOException {
        SearchRequest request = new SearchRequest("api-logs-test");
        SearchSourceBuilder sourceBuilder = new SearchSourceBuilder()
                .query(QueryBuilders.matchAllQuery())
                .size(100);
        request.source(sourceBuilder);
        return client.search(request, RequestOptions.DEFAULT);
    }
}
