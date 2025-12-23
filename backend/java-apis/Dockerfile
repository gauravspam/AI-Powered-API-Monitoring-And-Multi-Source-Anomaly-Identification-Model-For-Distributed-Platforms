# Multi-stage build for Spring Boot Backend
# Using Java 21 LTS for both build and runtime (stable and production-ready)
FROM eclipse-temurin:21-jdk AS build

# Install Gradle
WORKDIR /opt
RUN apt-get update && apt-get install -y wget unzip && rm -rf /var/lib/apt/lists/* && \
    wget -q https://services.gradle.org/distributions/gradle-8.14.3-bin.zip && \
    unzip gradle-8.14.3-bin.zip && \
    rm gradle-8.14.3-bin.zip && \
    mv gradle-8.14.3 gradle

ENV PATH=/opt/gradle/bin:$PATH

WORKDIR /app

# Copy Gradle files
COPY build.gradle settings.gradle ./
COPY gradle ./gradle

# Download dependencies (cached layer)
RUN gradle dependencies --no-daemon || true

# Copy source code
COPY src ./src

# Build the application
RUN gradle build --no-daemon -x test

# Runtime stage - Use Java 21 JRE (LTS)
FROM eclipse-temurin:21-jre

# Install curl for health check
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create non-root user
RUN groupadd -r spring && useradd -r -g spring spring

# Copy built JAR from build stage
COPY --from=build /app/build/libs/*.jar app.jar

# Change ownership
RUN chown spring:spring app.jar

# Switch to non-root user
USER spring:spring

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run the application
ENTRYPOINT ["java", "-jar", "app.jar"]

