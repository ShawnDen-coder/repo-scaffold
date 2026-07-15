use async_trait::async_trait;
use sqlx::PgPool;

use super::model::HealthCheck;
use crate::common::error::AppError;

/// Trait representing the repository contract for health check data.
#[async_trait]
pub trait HealthRepository: Send + Sync {
    /// Performs a database ping to verify connectivity.
    async fn ping(&self, pool: &PgPool) -> Result<(), sqlx::Error>;
}
