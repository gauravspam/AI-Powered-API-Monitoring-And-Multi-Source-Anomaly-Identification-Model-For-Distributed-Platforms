FROM eclipse-temurin:21-jdk AS build

WORKDIR /opt
RUN apt-get update && apt-get install -y wget unzip && rm -rf /var/lib/apt/lists/* && \
    wget -q https://services.gradle.org/distributions/gradle-8.8-bin.zip && \
    unzip gradle-8.8-bin.zip && rm gradle-8.8-bin.zip && mv gradle-8.8 gradle
ENV PATH=/opt/gradle/bin:$PATH

WORKDIR /app

# Essential configs only
COPY build.gradle settings.gradle ./
COPY src ./src

# Build (uses global Gradle)
RUN gradle build --no-daemon -x test

# Runtime
FROM eclipse-temurin:21-jre
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN groupadd -r spring && useradd -r -g spring spring
COPY --from=build /app/build/libs/*.jar app.jar
RUN chown spring:spring app.jar
USER spring
EXPOSE 8081
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8081/health || exit 1
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
