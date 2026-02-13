package com.api.monitoring.backend.dto.ml;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class LogEventDto {
    private Long timestamp;
    private String message;
    private String level;
    private String template_id;
}
