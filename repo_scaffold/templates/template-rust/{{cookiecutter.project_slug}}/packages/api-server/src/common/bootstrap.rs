use std::sync::Arc;

use sqlx::PgPool;

use crate::common::config::Config;
use crate::domains::health::{HealthService, HealthServiceTrait};

use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

/// Constructs and wires all application services and returns a configured AppState.
pub fn build_app_state(pool: PgPool, config: Config) -> AppState {
    let health_service: Arc<dyn HealthServiceTrait> = HealthService::create_service(pool.clone());

    AppState::new(config, health_service)
}

use super::app_state::AppState;

/// Setup tracing for the application.
/// This function initializes the tracing subscriber with a default filter and formatting.
pub fn setup_tracing() {
    dotenvy::dotenv().ok();

    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info,sqlx=info,tower_http=info,axum::rejection=trace".into()),
        )
        .with(
            tracing_subscriber::fmt::layer()
                .with_file(true)
                .with_line_number(true)
                .with_thread_ids(true)
                .with_thread_names(true)
                .with_target(true)
                .with_span_events(tracing_subscriber::fmt::format::FmtSpan::CLOSE),
        )
        .init();
}

/// Shutdown signal handler.
/// Listens for CTRL+C and logs a message when received.
pub async fn shutdown_signal() {
    tokio::signal::ctrl_c()
        .await
        .expect("Failed to install CTRL+C signal handler");
}
