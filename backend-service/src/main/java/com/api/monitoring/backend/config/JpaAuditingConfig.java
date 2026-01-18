package com.api.monitoring.backend.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;

/**
 * JPA Auditing Configuration
 * 
 * Enables automatic population of @CreatedDate and @LastModifiedDate fields.
 * This is the enterprise standard for handling audit timestamps.
 * 
 * Benefits:
 * - No manual timestamp management
 * - Consistent across all entities
 * - Thread-safe
 * - Transaction-aware
 */
@Configuration
@EnableJpaAuditing
public class JpaAuditingConfig {
    // Spring Data JPA automatically handles createdAt and updatedAt timestamps
}
