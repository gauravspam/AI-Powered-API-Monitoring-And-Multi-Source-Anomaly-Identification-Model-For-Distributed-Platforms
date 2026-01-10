FROM eclipse-temurin:21-jre
WORKDIR /app

# Copy pre-built JAR (build locally first)
COPY java-apis/build/libs/*.jar app.jar

# Non-root user
RUN groupadd -r spring && useradd -r -g spring spring && chown spring:spring /app
USER spring

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
