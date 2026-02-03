
package com.api.monitoring.backend.service;



public class AnomalyProcessingException extends RuntimeException {

    public AnomalyProcessingException(String message) {

        super(message);

    }

    public AnomalyProcessingException(String message, Throwable cause) {

        super(message, cause);

    }

}

