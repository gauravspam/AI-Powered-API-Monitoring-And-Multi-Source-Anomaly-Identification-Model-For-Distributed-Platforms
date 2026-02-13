package com.api.monitoring.backend.dto.ml;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Data;
import java.util.List;
import java.util.Map;

@Data
@Builder
public class PredictionWindowDto {
    @JsonProperty("window_start")
    private Long windowStart;

    @JsonProperty("window_end")
    private Long windowEnd;

    @JsonProperty("entity_id")
    private String entityId;

    private Map<String, List<MetricPointDto>> metrics;
    private List<LogEventDto> logs;
    private List<TraceSpanDto> traces;
}
