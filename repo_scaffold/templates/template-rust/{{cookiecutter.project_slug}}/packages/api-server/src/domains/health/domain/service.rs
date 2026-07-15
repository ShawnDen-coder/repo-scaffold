use std::sync::Arc;

use async_trait::async_trait;
use sqlx::PgPool;

use crate::common::error::AppError;

use super::model::HealthCheck;
use crate::domains::health::dto::health_dto::HealthResponse;

/// Trait defining the contract for health-check operations.
#[async_trait]
pub trait HealthServiceTrait: Send + Sync {
    /// Constructor for the service.
    fn create_service(pool: PgPool) -> Arc<dyn HealthServiceTrait>
    where
        Self: Sized;

    /// Checks the health of the application and its dependencies.
    async fn check_health(&self) -> Result<HealthResponse, AppError>;
}
