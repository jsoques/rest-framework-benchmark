## Context

The benchmark already has four working services (FastAPI+Uvicorn, FastAPI+Granian, Robyn, Go Fiber) and a shared `bench/run.py` harness. The goal is to add a fifth Rust implementation so the chart can compare a compiled, async, zero-cost-abstraction stack on the same endpoint. See `proposal.md` for motivation.

## Goals / Non-Goals

**Goals:**
- Add a `rust-axum/` service on port `8005` with the same `GET /spatial_ref_sys` contract as the existing services.
- Support `?static=1` (in-memory) and `?limit=<n>` (payload size) query parameters.
- Use a PostgreSQL connection pool capped at 50 connections.
- Integrate with the existing `bench/run.py` and `bench/report.py` without changing them beyond adding one entry.
- Update `README.md` with build/run instructions.

**Non-Goals:**
- Changing the database schema or the SQL query shape.
- Adding new benchmark modes or `wrk` parameters.
- Dockerising the Rust build.
- Benchmarking anything other than the existing `GET /spatial_ref_sys` endpoint.

## Decisions

### Axum + deadpool-postgres
- **Rationale:** Axum is the most common minimal, fast, tokio-based web framework in the Rust ecosystem. `deadpool-postgres` provides an async connection pool with a configurable `max_size` and uses `tokio-postgres` underneath, which is close in spirit to `asyncpg` used by the Python services.
- **Alternatives considered:** `actix-web` (slightly heavier) and `rocket` (more opinionated, compile-time macros). Both work, but Axum keeps the comparison focused on raw HTTP/JSON speed.

### `dotenvy` for `.env` loading
- **Rationale:** `dotenvy` is the maintained Rust port of `dotenv` and lets the binary read the root `.env` at startup without requiring the user to export variables manually.
- **Alternative:** Read from the environment only. Loading `.env` keeps parity with the Python services and the existing workflow.

### Query parameter `?static=1` and `?limit=<n>`
- **Rationale:** These are already implemented in the four existing services. Reusing the same contract lets `bench/run.py` treat the Rust service identically and allows direct framework-to-framework comparison in both DB and static modes.

### Port `8005`
- **Rationale:** The existing ports are `8001`–`8004`. `8005` is the next free port and avoids conflicts.

## Risks / Trade-offs

- **Compile time:** `cargo build --release` will take longer than the Python or Go builds on the first run. The release binary is then cached.
- **Binary size:** Release binaries are large, but they are gitignored and the `Cargo.lock`/`Cargo.toml` plus source are tracked.
- **Toolchain availability:** The user must have `cargo` and `rustc` installed. This is documented in `README.md`.
- **JSON null handling:** `tokio-postgres` returns `Option<T>` for nullable columns. The `SpatialRef` struct uses `Option<String>` and `Option<i64>` and `serde` serialises `None` as `null`, matching the other services.

## Open Questions

None. The scope and constraints are clear from the existing benchmark.
