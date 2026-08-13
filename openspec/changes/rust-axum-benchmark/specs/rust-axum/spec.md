## Purpose

Provides a Rust/Axum implementation of the common `GET /spatial_ref_sys` benchmark endpoint so that Rust's HTTP and JSON performance can be compared against FastAPI, Robyn, and Go Fiber under identical load conditions.

## ADDED Requirements

### Requirement: Common endpoint on the Rust service
The Rust service SHALL expose exactly one `GET /spatial_ref_sys` route on the port defined by `RUST_AXUM_PORT`.

#### Scenario: Endpoint is reachable
- **WHEN** a client sends a `GET` request to `http://<service-host>:<RUST_AXUM_PORT>/spatial_ref_sys`
- **THEN** the service responds with HTTP status `200 OK`

### Requirement: Database query is identical and parameterised
The endpoint SHALL execute `SELECT srid, auth_name, auth_srid, srtext, proj4text FROM spatial_ref_sys LIMIT $1` with a server-side bound limit value, defaulting to `100` and clamped to the range `1`–`1000`.

#### Scenario: Default query returns 100 rows
- **WHEN** the `GET /spatial_ref_sys` endpoint is called without a `limit` parameter
- **THEN** the response body contains a JSON array of exactly 100 objects

#### Scenario: Query limit can be overridden
- **WHEN** the endpoint is called with `?limit=250`
- **THEN** the response body contains a JSON array of exactly 250 objects

### Requirement: Response is a JSON array of objects
The endpoint SHALL return `Content-Type: application/json` and a top-level JSON array of objects, where each object contains the keys `srid`, `auth_name`, `auth_srid`, `srtext`, and `proj4text`.

#### Scenario: Response shape is correct
- **WHEN** the endpoint returns a successful response
- **THEN** each element in the array is an object whose keys match the selected columns and whose values are the row data or `null` where the column is null

### Requirement: Database connections are pooled
The service SHALL connect to PostgreSQL through `deadpool-postgres` and configure the pool with a maximum of 50 open connections.

#### Scenario: Concurrent requests share the pool
- **WHEN** 200 concurrent clients request the endpoint
- **THEN** the service uses the configured connection pool to serve the queries without opening a new connection per request

### Requirement: In-memory static mode
The service SHALL pre-load 100 rows from the database on startup and return them from memory when `?static=1` is present, without touching the database.

#### Scenario: Static mode bypasses the database
- **WHEN** a client calls `GET /spatial_ref_sys?static=1`
- **THEN** the service responds with HTTP status `200 OK` and the same 100 cached objects as quickly as possible

### Requirement: Configuration lives in the shared `.env`
The database connection string and listening port SHALL be read from the `.env` file in the repo root, and the service SHALL follow the same `.gitignore` and credential-handling rules as the other services.

#### Scenario: Service reads environment on startup
- **WHEN** the service starts
- **THEN** it reads the database connection string from `DATABASE_URL` and its own listening port from `RUST_AXUM_PORT`

### Requirement: Benchmark harness recognises the new service
`bench/run.py` SHALL start and stop the Rust service alongside the other services and `wrk` SHALL run against it with the same default parameters.

#### Scenario: Harness runs the Rust service
- **WHEN** `bench/run.py` is executed
- **THEN** it starts the Rust service on `RUST_AXUM_PORT`, waits for the port, runs `wrk`, captures the output, and stops the service
