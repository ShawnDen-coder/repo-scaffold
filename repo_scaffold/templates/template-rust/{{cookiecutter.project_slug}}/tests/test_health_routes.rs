use axum::http::{Method, StatusCode};
use {{cookiecutter.crate_name}}::{
    app::create_router,
    common::{
        bootstrap::build_app_state,
        config::Config,
        dto::RestApiResponse,
    },
};
use http_body_util::BodyExt;
use sqlx::postgres::PgPoolOptions;
use tower::ServiceExt;

async fn create_test_router() -> axum::Router {
    dotenvy::from_filename(".env.test").ok();
    let config = Config::from_env().unwrap();
    let pool = PgPoolOptions::new()
        .max_connections(config.database_max_connections)
        .min_connections(config.database_min_connections)
        .connect(&config.database_url)
        .await
        .unwrap();
    let state = build_app_state(pool, config.clone());
    create_router(state)
}

#[tokio::test]
async fn test_health_check() {
    let app = create_test_router().await;

    let request = axum::http::Request::builder()
        .method(Method::GET)
        .uri("/health")
        .header("Content-Type", "application/json")
        .body(axum::body::Body::empty())
        .unwrap();

    let response = app.oneshot(request).await.unwrap();

    assert_eq!(response.status(), StatusCode::OK);

    let body = response.into_body();
    let bytes = body.collect().await.unwrap().to_bytes();
    let response_body: RestApiResponse<serde_json::Value> =
        serde_json::from_slice(&bytes).unwrap();

    assert_eq!(response_body.0.status, 200);
    assert_eq!(response_body.0.data.unwrap()["status"], "ok");
}
