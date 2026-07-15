use axum::{
    body::Body,
    error_handling::HandleErrorLayer,
    http::{
        header::{AUTHORIZATION, CONTENT_TYPE},
        Method, StatusCode,
    },
    middleware, Router,
};
use std::time::Duration;
use tower::ServiceBuilder;
use tower_http::{
    cors::{Any, CorsLayer},
    trace::TraceLayer,
};

{% if cookiecutter.use_openapi == 'yes' %}
use utoipa::OpenApi;
use utoipa_swagger_ui::SwaggerUi;
{% endif %}

use crate::{
    common::{
        app_state::AppState,
        error::handle_error,
    },
    domains::health::{health_routes{% if cookiecutter.use_openapi == 'yes' %}, HealthApiDoc{% endif %}},
};

{% if cookiecutter.use_openapi == 'yes' %}
fn create_swagger_ui() -> SwaggerUi {
    SwaggerUi::new("/docs").url(
        "/api-docs/health/openapi.json",
        HealthApiDoc::openapi(),
    )
}
{% endif %}

pub fn create_router(state: AppState) -> Router {
    let cors = CorsLayer::new()
        .allow_methods([Method::GET, Method::POST, Method::PUT, Method::DELETE])
        .allow_origin(Any)
        .allow_headers([AUTHORIZATION, CONTENT_TYPE]);

    let middleware_stack = ServiceBuilder::new()
        .layer(HandleErrorLayer::new(handle_error))
        .timeout(Duration::from_secs(1800))
        .layer(cors);

    // Health routes (public)
    let health_router = Router::new().nest("", health_routes());

    Router::new()
        .merge(health_router)
        {% if cookiecutter.use_openapi == 'yes' %}
        .merge(create_swagger_ui())
        {% endif %}
        .layer(
            TraceLayer::new_for_http()
                .make_span_with(|req: &axum::http::Request<_>| {
                    tracing::info_span!(
                        "request",
                        method = %req.method(),
                        uri = %req.uri(),
                    )
                })
                .on_response(
                    |response: &axum::http::Response<_>,
                     latency: std::time::Duration,
                     _span: &tracing::Span| {
                        tracing::info!(
                            "request completed: status = {status}, latency = {latency:?}",
                            status = response.status(),
                            latency = latency
                        );
                    },
                ),
        )
        .fallback(fallback)
        .layer(middleware_stack)
        .with_state(state)
}

/// Fallback handler for unmatched routes.
pub async fn fallback() -> Result<impl axum::response::IntoResponse, crate::common::error::AppError> {
    Ok((StatusCode::NOT_FOUND, "Not Found"))
}
