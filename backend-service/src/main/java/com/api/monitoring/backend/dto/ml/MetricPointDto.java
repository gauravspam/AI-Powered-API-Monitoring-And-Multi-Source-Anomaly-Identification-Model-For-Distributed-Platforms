package com.api.monitoring.backend.dto.ml;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class MetricPointDto {
    private Long timestamp;
    private Double value;
}
