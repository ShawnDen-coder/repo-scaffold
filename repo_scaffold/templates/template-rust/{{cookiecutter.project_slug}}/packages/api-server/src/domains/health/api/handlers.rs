use crate::common::{
    app_state::AppState,
    dto::RestApiResponse,
};
use axum::extract::State;
use axum::response::IntoResponse;

use crate::domains::health::dto::health_dto::HealthResponse;

/// Health check endpoint.
/// Returns a simple status response to indicate the service is running.
{% if cookiecutter.use_openapi == 'yes' %}
#[utoipa::path(
    get,
    path = "/health",
    responses((status = 200, description = "Health check", body = HealthResponse)),
    tag = "Health"
)]
{% endif %}
pub async fn health_check(
    State(state): State<AppState>,
) -> Result<impl IntoResponse, crate::common::error::AppError> {
    let status = state.health_service.check_health().await?;
    Ok(RestApiResponse::success(status))
}
