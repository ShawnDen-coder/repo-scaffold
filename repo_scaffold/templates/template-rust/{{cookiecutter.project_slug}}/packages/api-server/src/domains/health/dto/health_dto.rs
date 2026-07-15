use serde::{Deserialize, Serialize};
{% if cookiecutter.use_openapi == 'yes' %}
use utoipa::ToSchema;
{% endif %}

/// Health check response DTO.
#[derive(Debug, Clone, Serialize, Deserialize{% if cookiecutter.use_openapi == 'yes' %}, ToSchema{% endif %})]
pub struct HealthResponse {
    pub status: String,
    pub version: String,
    pub database: String,
}
