mod api {
    mod handlers;
    pub mod routes;
}

mod domain {
    pub mod model;
    pub mod repository;
    pub mod service;
}

pub mod dto {
    pub mod health_dto;
}

mod infra {
    mod impl_repository;
    pub mod impl_service;
}

// Re-export commonly used items for convenience
pub use api::routes::{health_routes{% if cookiecutter.use_openapi == 'yes' %}, HealthApiDoc{% endif %}};
pub use domain::service::HealthServiceTrait;
pub use infra::impl_service::HealthService;
