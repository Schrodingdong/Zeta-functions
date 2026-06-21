FROM openjdk:25-ea AS build
LABEL authors="Schrodi"
WORKDIR /zeta-runner
COPY . .
RUN ./mvnw clean install -DskipTests

FROM openjdk:25-ea-slim AS run
LABEL authors="Schrodi"
WORKDIR /zeta-runner
COPY --from=build /zeta-runner/target/zeta-runner-0.0.1-SNAPSHOT.jar .
EXPOSE 8080
CMD ["java", "-jar", "zeta-runner-0.0.1-SNAPSHOT.jar"]
