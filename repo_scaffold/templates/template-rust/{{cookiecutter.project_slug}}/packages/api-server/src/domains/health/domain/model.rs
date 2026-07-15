use serde::{Deserialize, Serialize};
{% if cookiecutter.use_openapi == 'yes' %}
use utoipa::ToSchema;
{% endif %}

/// Represents a health check response.
#[derive(Debug, Clone, Serialize, Deserialize{% if cookiecutter.use_openapi == 'yes' %}, ToSchema{% endif %})]
pub struct HealthCheck {
    pub status: String,
    pub version: String,
}
