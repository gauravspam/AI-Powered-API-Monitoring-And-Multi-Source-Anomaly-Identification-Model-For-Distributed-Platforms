FROM eclipse-temurin:21-jdk AS build

WORKDIR /opt
RUN apt-get update && apt-get install -y wget unzip && rm -rf /var/lib/apt/lists/* && \
    wget -q https://services.gradle.org/distributions/gradle-8.8-bin.zip && \
    unzip gradle-8.8-bin.zip && rm gradle-8.8-bin.zip && mv gradle-8.8 gradle
ENV PATH=/opt/gradle/bin:$PATH

WORKDIR /app

# Copy Gradle files
COPY build.gradle settings.gradle gradle.properties ./

# Copy ALL source code
COPY src ./src

# Build the application
RUN gradle build --no-daemon -x test

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
