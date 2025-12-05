FROM golang:1.24-alpine

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

EXPOSE 8080

# Default command (can be overridden in docker-compose.yml)
CMD ["go", "run", "cmd/api/main.go"]