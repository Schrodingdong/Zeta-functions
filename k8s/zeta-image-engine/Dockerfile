FROM docker:dind
LABEL author="Schrodi"

# Install Go
COPY --from=golang:1.26-alpine /usr/local/go/ /usr/local/go/
ENV PATH="/usr/local/go/bin:${PATH}"

# Copy code
WORKDIR /zeta
COPY go.mod go.sum ./
RUN go mod download
COPY src src

# Build
ENV DOCKER_CONTENT_TRUST=0
RUN go build -C src -o /zeta/image-engine
EXPOSE 8080

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]