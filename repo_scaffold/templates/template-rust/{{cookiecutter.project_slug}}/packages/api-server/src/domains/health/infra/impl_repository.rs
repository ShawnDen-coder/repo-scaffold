use async_trait::async_trait;
use sqlx::PgPool;

use crate::domains::health::domain::repository::HealthRepository;

pub struct HealthRepo;

#[async_trait]
impl HealthRepository for HealthRepo {
    async fn ping(&self, pool: &PgPool) -> Result<(), sqlx::Error> {
        sqlx::query("SELECT 1")
            .execute(pool)
            .await?;
        Ok(())
    }
}
