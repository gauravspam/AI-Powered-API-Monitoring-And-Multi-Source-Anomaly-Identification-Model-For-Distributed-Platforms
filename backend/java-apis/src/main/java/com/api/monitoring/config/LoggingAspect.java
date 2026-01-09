package com.api.monitoring.config;

import com.api.monitoring.annotation.LogApiCall;
import com.api.monitoring.service.LoggingService;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import jakarta.servlet.http.HttpServletRequest;
import java.util.HashMap;
import java.util.Map;

/**
 * AOP Aspect for automatic API call logging
 * Intercepts all methods annotated with @LogApiCall
 */
@Aspect
@Component
public class LoggingAspect {
    
    private static final Logger LOGGER = 
        LoggerFactory.getLogger(LoggingAspect.class);
    
    @Autowired
    private LoggingService loggingService;
    
    @Around("@annotation(com.api.monitoring.annotation.LogApiCall)")
    public Object logApiExecution(ProceedingJoinPoint pjp) 
            throws Throwable {
        
        long startTime = System.currentTimeMillis();
        MethodSignature signature = (MethodSignature) pjp.getSignature();
        String methodName = signature.getMethod().getName();
        
        ServletRequestAttributes attributes = 
            (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
        
        String endpoint = "/api/unknown";
        String method = "UNKNOWN";
        int statusCode = 500;
        
        try {
            if (attributes != null) {
                HttpServletRequest request = attributes.getRequest();
                endpoint = request.getRequestURI();
                method = request.getMethod();
            }
            
            Object result = pjp.proceed();
            long duration = System.currentTimeMillis() - startTime;
            statusCode = 200;
            
            Map<String, Object> metadata = new HashMap<>();
            metadata.put("class_name", signature.getDeclaringType().getSimpleName());
            metadata.put("method_name", methodName);
            
            loggingService.logApiCall(
                endpoint,
                method,
                statusCode,
                duration,
                metadata
            );
            
            LOGGER.info("API Call: {} {} - {} ms - Status: {}",
                method, endpoint, duration, statusCode);
            
            return result;
            
        } catch (Exception e) {
            long duration = System.currentTimeMillis() - startTime;
            statusCode = 500;
            
            loggingService.logApiError(
                endpoint,
                method,
                statusCode,
                e.getMessage(),
                duration
            );
            
            LOGGER.error("API Call Error: {} {} - {} ms - {}",
                method, endpoint, duration, e.getMessage(), e);
            
            throw e;
        }
    }
}
