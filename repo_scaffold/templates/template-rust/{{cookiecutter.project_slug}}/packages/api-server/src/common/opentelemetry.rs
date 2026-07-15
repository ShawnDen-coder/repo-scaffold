use opentelemetry::trace::TracerProvider;
use opentelemetry_appender_tracing::layer::OpenTelemetryTracingBridge;
use opentelemetry_sdk::trace::SdkTracerProvider;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter, Layer};

/// Setup tracing with OpenTelemetry export.
/// Initializes the OTLP exporter and bridges it with the `tracing` crate.
pub fn setup_tracing_opentelemetry() -> SdkTracerProvider {
    dotenvy::dotenv().ok();

    let exporter = opentelemetry_otlp::new_exporter().http();
    let tracer_provider = opentelemetry_sdk::trace::TracerProvider::builder()
        .with_simple_exporter(exporter)
        .build();
    let tracer = tracer_provider.tracer("{{cookiecutter.crate_name}}");

    let otel_layer = tracing_opentelemetry::layer().with_tracer(tracer);

    let logger_provider = opentelemetry_sdk::logs::LoggerProvider::builder()
        .with_simple_exporter(opentelemetry_otlp::new_exporter().http())
        .build();

    let otel_log_layer = OpenTelemetryTracingBridge::new(&logger_provider);

    let fmt_layer = tracing_subscriber::fmt::layer()
        .with_file(true)
        .with_line_number(true)
        .with_thread_ids(true)
        .with_thread_names(true)
        .with_target(true)
        .with_span_events(tracing_subscriber::fmt::format::FmtSpan::CLOSE);

    let env_filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| "info,sqlx=info,tower_http=info,axum::rejection=trace".into());

    tracing_subscriber::registry()
        .with(env_filter)
        .with(fmt_layer)
        .with(otel_layer)
        .with(otel_log_layer)
        .init();

    tracer_provider
}

/// Shutdown OpenTelemetry providers gracefully.
pub fn shutdown_opentelemetry(tracer_provider: SdkTracerProvider) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    tracer_provider.shutdown()?;
    Ok(())
}
