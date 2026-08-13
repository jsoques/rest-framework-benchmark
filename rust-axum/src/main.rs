use std::env;

use axum::extract::{Query, State};
use axum::http::StatusCode;
use axum::routing::get;
use axum::{Json, Router};
use deadpool_postgres::{Manager, Pool};
use serde::{Deserialize, Serialize};
use tokio_postgres::NoTls;

const QUERY: &str = "SELECT srid, auth_name, auth_srid, srtext, proj4text FROM spatial_ref_sys LIMIT $1";

#[derive(Clone, Serialize)]
struct SpatialRef {
    srid: i32,
    auth_name: Option<String>,
    auth_srid: Option<i32>,
    srtext: Option<String>,
    proj4text: Option<String>,
}

#[derive(Clone)]
struct AppState {
    pool: Pool,
    cached: Vec<SpatialRef>,
}

#[derive(Deserialize)]
struct Params {
    #[serde(default, rename = "static")]
    static_mode: Option<String>,
    limit: Option<String>,
}

fn row_to_ref(row: &tokio_postgres::Row) -> SpatialRef {
    SpatialRef {
        srid: row.get(0),
        auth_name: row.get(1),
        auth_srid: row.get(2),
        srtext: row.get(3),
        proj4text: row.get(4),
    }
}

fn parse_limit(value: Option<&String>, default: i64) -> i64 {
    match value {
        Some(s) => match s.parse::<i64>() {
            Ok(n) if n < 1 => 1,
            Ok(n) if n > 1000 => 1000,
            Ok(n) => n,
            Err(_) => default,
        },
        None => default,
    }
}

async fn spatial_ref_sys(
    State(state): State<AppState>,
    Query(params): Query<Params>,
) -> Result<Json<Vec<SpatialRef>>, (StatusCode, String)> {
    if params.static_mode.as_deref() == Some("1") {
        return Ok(Json(state.cached));
    }

    let limit = parse_limit(params.limit.as_ref(), 100);
    let client = state
        .pool
        .get()
        .await
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

    let rows = client
        .query(QUERY, &[&limit])
        .await
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

    let records: Vec<SpatialRef> = rows.iter().map(row_to_ref).collect();
    Ok(Json(records))
}

#[tokio::main]
async fn main() {
    dotenvy::dotenv().ok();

    let database_url = env::var("DATABASE_URL").expect("DATABASE_URL must be set");
    let port = env::var("RUST_AXUM_PORT").unwrap_or_else(|_| "8005".to_string());

    let pg_config: tokio_postgres::Config = database_url
        .parse()
        .expect("DATABASE_URL must be a valid postgres connection string");

    let manager = Manager::new(pg_config, NoTls);
    let pool = Pool::builder(manager)
        .max_size(50)
        .build()
        .expect("Failed to create connection pool");

    // Pre-load cache for the static mode
    let client = pool
        .get()
        .await
        .expect("Failed to get a database client for cache warm-up");
    let default_limit: i64 = 100;
    let cached_rows = client
        .query(QUERY, &[&default_limit])
        .await
        .expect("Failed to warm the in-memory cache");
    let cached: Vec<SpatialRef> = cached_rows.iter().map(row_to_ref).collect();

    let state = AppState { pool, cached };
    let app = Router::new()
        .route("/spatial_ref_sys", get(spatial_ref_sys))
        .with_state(state);

    let listener = tokio::net::TcpListener::bind(format!("0.0.0.0:{}", port))
        .await
        .expect("Failed to bind to port");
    axum::serve(listener, app)
        .await
        .expect("Server failed");
}
