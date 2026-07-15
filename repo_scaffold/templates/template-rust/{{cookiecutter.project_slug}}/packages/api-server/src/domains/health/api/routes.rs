use crate::common::app_state::AppState;
use axum::{routing::get, Router};

use super::handlers;
{% if cookiecutter.use_openapi == 'yes' %}
use utoipa::OpenApi;
use crate::domains::health::dto::health_dto::HealthResponse;

/// OpenAPI documentation for health routes.
#[derive(OpenApi)]
#[openapi(
    paths(super::handlers::health_check),
    components(schemas(HealthResponse)),
    tags((name = "Health", description = "Health check endpoints"))
)]
pub struct HealthApiDoc;
{% endif %}

/// Creates a router for the health check routes.
pub fn health_routes() -> Router<AppState> {
    Router::new().route("/health", get(handlers::health_check))
}
