package com.api.monitoring.backend.config;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Configuration;
import org.apache.http.auth.AuthScope;
import org.apache.http.auth.UsernamePasswordCredentials;
import org.apache.http.impl.client.BasicCredentialsProvider;
import org.apache.http.ssl.SSLContexts;
import org.opensearch.client.RestClient;
import org.opensearch.client.RestHighLevelClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import jakarta.annotation.PostConstruct;
import javax.net.ssl.SSLContext;

@ConditionalOnProperty(name = "opensearch.enabled", havingValue = "true", matchIfMissing = false)
@Configuration
public class OpenSearchConfig {

    private static final Logger logger = LoggerFactory.getLogger(OpenSearchConfig.class);

    @Value("${opensearch.host}")
    private String host;

    @Value("${opensearch.port}")
    private int port;

    @Value("${opensearch.scheme}")
    private String scheme;

    @Value("${opensearch.username}")
    private String username;

    @Value("${opensearch.password}")
    private String password;

    @PostConstruct
    public void init() {
        logger.info("========================================");
        logger.info("OpenSearchConfig @PostConstruct called!");
        logger.info("Host: {}, Port: {}, Scheme: {}", host, port, scheme);
        logger.info("========================================");
    }

    @Bean(name = "openSearchClient", destroyMethod = "close")
    public RestHighLevelClient openSearchClient() {
        try {
            logger.info("=== BEAN METHOD: Creating OpenSearch RestHighLevelClient ===");
            logger.info("Host: {}, Port: {}, Scheme: {}", host, port, scheme);
            
            var credentialsProvider = new BasicCredentialsProvider();
            credentialsProvider.setCredentials(AuthScope.ANY,
                    new UsernamePasswordCredentials(username, password));

            SSLContext sslContext = SSLContexts.custom()
                    .loadTrustMaterial((chain, authType) -> true)
                    .build();

            RestHighLevelClient client = new RestHighLevelClient(
                    RestClient.builder(new org.apache.http.HttpHost(host, port, scheme))
                            .setHttpClientConfigCallback(httpClientBuilder -> httpClientBuilder
                                    .setDefaultCredentialsProvider(credentialsProvider)
                                    .setSSLContext(sslContext)));
            
            logger.info("✓ OpenSearch RestHighLevelClient created successfully");
            return client;
            
        } catch (Exception e) {
            logger.error("✗ Failed to create OpenSearch client", e);
            throw new RuntimeException("Failed to initialize OpenSearch client", e);
        }
    }
}
