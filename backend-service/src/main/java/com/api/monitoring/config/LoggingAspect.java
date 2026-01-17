// backend/java-apis/src/main/java/com/api/monitoring/config/LoggingAspect.java

package com.api.monitoring.config;

import com.api.monitoring.annotation.LogApiCall;
// import com.api.monitoring.service.LoggingService;  // ← Comment out
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
// import org.springframework.beans.factory.annotation.Autowired;  // ← Comment out
import org.springframework.stereotype.Component;

@Aspect
@Component
public class LoggingAspect {

  private static final Logger logger = LoggerFactory.getLogger(LoggingAspect.class);

  // @Autowired // ← Comment out
  // private LoggingService loggingService; // ← Comment out

  @Around("@annotation(logApiCall)")
  public Object logApiCall(ProceedingJoinPoint joinPoint, LogApiCall logApiCall) throws Throwable {
    String methodName = joinPoint.getSignature().getName();
    String className = joinPoint.getTarget().getClass().getName();

    long startTime = System.currentTimeMillis();

    try {
      Object result = joinPoint.proceed();
      long executionTime = System.currentTimeMillis() - startTime;

      logger.info("API Call: {}.{} executed in {} ms", className, methodName, executionTime);

      // Remove service logging
      return result;

    } catch (Exception e) {
      long executionTime = System.currentTimeMillis() - startTime;

      logger.error("API Call Failed: {}.{} after {} ms - Error: {}",
          className, methodName, executionTime, e.getMessage());

      // Remove service error logging
      throw e;
    }
  }
}
