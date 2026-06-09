FROM golang:1.26-alpine AS build
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY src src
RUN go build -C src -o /image-engine

FROM docker:dind AS run
LABEL author="Schrodi"
COPY --from=build /image-engine /image-engine
EXPOSE 8080
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]