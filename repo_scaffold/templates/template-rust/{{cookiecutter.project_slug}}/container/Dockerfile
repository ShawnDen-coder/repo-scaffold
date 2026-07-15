FROM rust:1.86-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y libssl-dev pkg-config curl

# Copy sources
COPY . .

# Copy SQLx query metadata for offline mode
COPY .sqlx .sqlx

# sqlx offline mode
ENV SQLX_OFFLINE=true

# Build in release mode
RUN cargo build --release

# Create runtime image
FROM debian:stable-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libssl3 ca-certificates curl && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/{{cookiecutter.crate_name}} .

# Copy and rename environment file
COPY --from=builder /app/.env.test .env

ENV RUST_LOG=info

ENTRYPOINT ["/app/{{cookiecutter.crate_name}}"]
