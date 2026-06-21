FROM openjdk:25-ea AS build
LABEL authors="Schrodi"
WORKDIR /zeta-apiserver
COPY . .
RUN ./mvnw clean install -DskipTests

FROM openjdk:25-ea-slim AS run
LABEL authors="Schrodi"
WORKDIR /zeta-apiserver
COPY --from=build /zeta-apiserver/target/zeta-apiserver-0.0.1-SNAPSHOT.jar .
EXPOSE 8080
CMD ["java", "-jar", "zeta-apiserver-0.0.1-SNAPSHOT.jar"]
