## Why

The existing benchmark compares Python and Go REST frameworks on a database-bound endpoint. Adding a Rust (Axum) implementation will expose how a zero-cost-abstraction, async, compiled stack performs on the same workload, both with and without Postgres latency.

## What Changes

- Add a new `rust-axum/` service that exposes `GET /spatial_ref_sys` using Axum, `tokio-postgres`, and `deadpool-postgres`.
- The service will support the same `?static=1` in-memory mode and `?limit=<n>` payload-size control as the existing services.
- Add `RUST_AXUM_PORT=8005` to the root `.env`.
- Register the new service in `bench/run.py` and `bench/report.py` (automatically picked up by existing harness).
- Update `README.md` with setup and run instructions for the Rust service.

## Capabilities

### New Capabilities

- `rust-axum`: A Rust/Axum REST service that returns the `spatial_ref_sys` benchmark payload from PostgreSQL or an in-memory cache, with configurable `LIMIT`.

### Modified Capabilities

- None. This change only adds a new service; it does not alter existing behavior.

## Impact

- New Rust toolchain dependency (`cargo`, `rustc`) for building the service.
- New `rust-axum/Cargo.toml`, `rust-axum/src/main.rs`, and a release binary tracked in `.gitignore`.
- `bench/run.py` grows one entry in `SERVICES` and `SERVICE_PORTS`.
- `README.md` updated.
- No change to the database schema, `.env` format, or `wrk` invocation.
