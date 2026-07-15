# {{cookiecutter.project_slug}}

{{cookiecutter.description}}

## Features

- **Clean Architecture**: Clear separation of domain, infrastructure, and API layers
- **Modular Domains**: Self-contained feature modules under `src/domains/`
- **SQLx Integration**: Compile-time-checked queries with offline mode support
- **JWT Auth**: Secure authentication middleware (ready for you to add an auth domain)
{% if cookiecutter.use_openapi == 'yes' %}
- **OpenAPI Docs**: Swagger UI powered by Utoipa
{% endif %}
{% if cookiecutter.use_opentelemetry == 'yes' %}
- **Observability**: Optional OpenTelemetry tracing and metrics
{% endif %}
- **Testing**: Integration tests with `tokio::test` and `tower::ServiceExt`

## Project Structure

```text
├── Cargo.toml                          # Workspace root (virtual manifest)
├── packages/
│   └── api-server/                     # Main API server crate
│       ├── Cargo.toml
│       └── src/
│           ├── main.rs                 # Application entry point
│           ├── lib.rs                  # Module declarations
│           ├── app.rs                  # Router setup and middleware
│           ├── common/                 # Shared components and utilities
│           │   ├── app_state.rs        # AppState for dependency injection
│           │   ├── bootstrap.rs        # Service initialization
│           │   ├── config.rs           # Environment variable configuration
│           │   ├── dto.rs              # Shared DTOs (ApiResponse)
│           │   ├── error.rs            # AppError enum and error mappers
│           │   ├── jwt.rs              # JWT encoding, decoding, and auth middleware
│           │   └── ts_format.rs        # Custom timestamp serialization
│           └── domains/                # Feature modules
│               └── health/            # Health check (reference domain)
│                   ├── api/            # Route handlers and definitions
│                   ├── domain/         # Models, traits
│                   ├── dto/            # Data Transfer Objects
│                   └── infra/          # Infrastructure implementations
├── tests/                              # Integration tests
├── db-seed/                            # Database schema and seed data
├── .env                                # Environment variables
└── justfile                            # Task runner recipes
```

## Getting Started

### Prerequisites

- Rust (latest stable)
- PostgreSQL
{% if cookiecutter.use_docker == 'yes' %}
- Docker / Podman & Compose (optional)
{% endif %}

### Quickstart

**Manual Setup:**

1. Create the database and run migrations:

   ```bash
   psql -U testuser -d testdb -f db-seed/01-tables.sql
   ```

2. Configure environment variables in `.env`:

   ```env
   DATABASE_URL=postgres://testuser:pass@localhost:5432/testdb
   JWT_SECRET_KEY=your_super_secret_key
   SERVICE_PORT=8080
   ```

3. Run the server:

   ```bash
   cargo run
   ```

{% if cookiecutter.use_docker == 'yes' %}
**Using Docker Compose:**

```bash
podman compose -f container/compose.yaml up --build
```
{% endif %}

## Adding a New Domain

1. Create `src/domains/<feature>/` with `api/`, `domain/`, `dto/`, `infra/` subdirectories
2. Register in `src/domains/mod.rs`
3. Add the service to `AppState` in `common/app_state.rs`
4. Wire the service in `common/bootstrap.rs`
5. Add routes in `app.rs`

The `health` domain serves as a reference implementation you can copy.

## Architecture

- **Domain**: Traits and models define core business logic
- **Infra**: Concrete implementations (SQLx repositories, services)
- **API**: Axum handlers and route definitions
- **DTOs**: Typed request/response contracts
- **Bootstrap**: Wires dependencies into `AppState`

## Testing

```bash
cargo test
```

## Linting

```bash
just lint
```

{% if cookiecutter.use_openapi == 'yes' %}
## API Documentation

Open [http://localhost:8080/docs](http://localhost:8080/docs) for Swagger UI.
{% endif %}

{% if cookiecutter.use_opentelemetry == 'yes' %}
## OpenTelemetry

Run with OpenTelemetry enabled:

```bash
cargo run --features opentelemetry
```
{% endif %}

## License

MIT
