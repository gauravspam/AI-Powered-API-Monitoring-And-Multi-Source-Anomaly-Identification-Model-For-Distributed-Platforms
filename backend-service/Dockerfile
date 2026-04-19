FROM eclipse-temurin:21-jdk AS build

WORKDIR /app

# Copy Gradle wrapper and build descriptors first for better layer caching
COPY gradlew gradlew.bat build.gradle settings.gradle gradle.properties ./
COPY gradle ./gradle

# Copy the full project sources needed by the build
COPY src ./src

RUN chmod +x gradlew

# Build the application with project wrapper for deterministic Gradle version
RUN ./gradlew build --no-daemon -x test

# Runtime stage
FROM eclipse-temurin:21-jre
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN groupadd -r spring && useradd -r -g spring spring
# Copy the built JAR
COPY --from=build /app/build/libs/*.jar app.jar
RUN chown spring:spring app.jar
USER spring
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/actuator/health || curl -f http://localhost:8080/health || exit 1
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
