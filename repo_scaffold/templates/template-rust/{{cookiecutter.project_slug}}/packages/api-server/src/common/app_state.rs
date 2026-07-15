use std::sync::Arc;

use crate::domains::health::HealthServiceTrait;

use super::config::Config;

/// AppState holds the application-wide shared state.
/// It is passed to request handlers via Axum's extension mechanism.
#[derive(Clone)]
pub struct AppState {
    /// Global application configuration.
    pub config: Config,
    /// Service handling health-check logic.
    pub health_service: Arc<dyn HealthServiceTrait>,
}

impl AppState {
    /// Creates a new instance of AppState with the provided dependencies.
    pub fn new(config: Config, health_service: Arc<dyn HealthServiceTrait>) -> Self {
        Self {
            config,
            health_service,
        }
    }
}
