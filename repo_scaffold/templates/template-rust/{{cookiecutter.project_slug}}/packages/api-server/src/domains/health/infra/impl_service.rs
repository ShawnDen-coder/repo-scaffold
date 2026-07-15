use std::sync::Arc;

use async_trait::async_trait;
use sqlx::PgPool;

use crate::common::error::AppError;
use crate::domains::health::{
    domain::{repository::HealthRepository, service::HealthServiceTrait},
    dto::health_dto::HealthResponse,
    infra::impl_repository::HealthRepo,
};

/// Service for handling health-check logic.
#[derive(Clone)]
pub struct HealthService {
    pool: PgPool,
    repo: Arc<dyn HealthRepository + Send + Sync>,
}

#[async_trait]
impl HealthServiceTrait for HealthService {
    /// Constructor for the service.
    fn create_service(pool: PgPool) -> Arc<dyn HealthServiceTrait> {
        Arc::new(Self {
            pool,
            repo: Arc::new(HealthRepo {}),
        })
    }

    /// Checks the health of the application and its dependencies.
    async fn check_health(&self) -> Result<HealthResponse, AppError> {
        let db_status = match self.repo.ping(&self.pool).await {
            Ok(()) => "ok",
            Err(_) => "unavailable",
        };

        Ok(HealthResponse {
            status: "ok".to_string(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            database: db_status.to_string(),
        })
    }
}
