FROM eclipse-temurin:21-jre

WORKDIR /app

# Copy PRE-BUILT JAR (created by ./gradlew build)
COPY ../../backend/java-apis/build/libs/*.jar app.jar

# Install curl for healthcheck
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Non-root user (security)
RUN groupadd -r spring && \
    useradd -r -g spring spring && \
    chown spring:spring /app

USER spring

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
  CMD curl -f http://localhost:8080/actuator/health || exit 1

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
