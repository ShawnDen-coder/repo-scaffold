use axum::{
    extract::Request,
    middleware::Next,
    response::{IntoResponse, Response},
};

use chrono::{Duration, Utc};
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use std::sync::LazyLock;
use std::{env, fmt::Display};
{% if cookiecutter.use_openapi == 'yes' %}
use utoipa::ToSchema;
{% endif %}

use super::error::AppError;

/// JWT_SECRET_KEY is the environment variable that holds the secret key for JWT encoding and decoding.
pub static KEYS: LazyLock<Keys> = LazyLock::new(|| {
    dotenvy::dotenv().ok();

    let secret = env::var("JWT_SECRET_KEY").expect("JWT_SECRET_KEY must be set");
    Keys::new(secret.as_bytes())
});

/// Keys holds the encoding and decoding keys for JWT.
pub struct Keys {
    pub encoding: EncodingKey,
    pub decoding: DecodingKey,
}

impl Keys {
    fn new(secret: &[u8]) -> Self {
        Self {
            encoding: EncodingKey::from_secret(secret),
            decoding: DecodingKey::from_secret(secret),
        }
    }
}

/// Claims represents the claims in the JWT token.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,
    pub exp: usize,
    pub iat: usize,
}

impl Display for Claims {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "user_id: {}", self.sub)
    }
}

impl Default for Claims {
    fn default() -> Self {
        let now = Utc::now();
        let expire: Duration = Duration::hours(24);
        let exp: usize = (now + expire).timestamp() as usize;
        let iat: usize = now.timestamp() as usize;
        Claims {
            sub: String::new(),
            exp,
            iat,
        }
    }
}

/// AuthBody represents the authentication response body.
#[derive(Debug, Serialize, Deserialize{% if cookiecutter.use_openapi == 'yes' %}, ToSchema{% endif %})]
pub struct AuthBody {
    pub access_token: String,
    pub token_type: String,
}

impl AuthBody {
    pub fn new(access_token: String) -> Self {
        Self {
            access_token,
            token_type: "Bearer".to_string(),
        }
    }
}

/// AuthPayload represents the authentication request payload.
#[derive(Debug, Serialize, Deserialize{% if cookiecutter.use_openapi == 'yes' %}, ToSchema{% endif %})]
pub struct AuthPayload {
    pub client_id: String,
    pub client_secret: String,
}

/// make_jwt_token creates a JWT token for the given user ID.
pub fn make_jwt_token(user_id: &str) -> Result<String, AppError> {
    let claims = Claims {
        sub: user_id.to_string(),
        ..Default::default()
    };
    encode(&Header::default(), &claims, &KEYS.encoding).map_err(|_| AppError::TokenCreation)
}

/// Middleware to validate JWT tokens.
/// If the token is valid, the request proceeds; otherwise, a 401 Unauthorized is returned.
pub async fn jwt_auth<B>(mut req: Request<B>, next: Next) -> Result<Response, Response>
where
    B: Send + Into<axum::body::Body>,
{
    let token = req
        .headers()
        .get("Authorization")
        .and_then(|v| v.to_str().ok())
        .and_then(|header| header.strip_prefix("Bearer "))
        .map(|t| t.trim())
        .filter(|t| !t.is_empty())
        .ok_or_else(|| AppError::InvalidToken.into_response())?;

    let token_data =
        decode::<Claims>(token, &KEYS.decoding, &Validation::default()).map_err(|err| {
            tracing::error!("Error decoding token: {:?}", err);
            AppError::InvalidToken.into_response()
        })?;

    req.extensions_mut().insert(token_data.claims);
    Ok(next.run(req.map(Into::into)).await)
}
