## 1. Rust project scaffold

- [x] 1.1 Create `rust-axum/Cargo.toml` with dependencies: `axum`, `tokio`, `serde`, `serde_json`, `deadpool-postgres`, `tokio-postgres`, `dotenvy`
- [x] 1.2 Create `rust-axum/src/main.rs` with the Axum app, `deadpool-postgres` pool, `GET /spatial_ref_sys` handler, and `.env` loading
- [x] 1.3 Add a `.gitignore` rule (or update root `.gitignore`) to exclude `rust-axum/target/` and the compiled binary

## 2. Environment and benchmark integration

- [x] 2.1 Add `RUST_AXUM_PORT=8005` to the root `.env`
- [x] 2.2 Add `RUST_AXUM_PORT` and the `rust-axum` start command to `bench/run.py`
- [x] 2.3 Update `README.md` with Rust toolchain setup, `cargo build --release`, and manual run instructions

## 3. Build and verification

- [x] 3.1 Build `rust-axum` in release mode
- [x] 3.2 Start the Rust service and `curl` `GET /spatial_ref_sys` to assert 100 objects
- [x] 3.3 `curl` `GET /spatial_ref_sys?static=1` and assert 100 objects
- [x] 3.4 `curl` `GET /spatial_ref_sys?limit=250` and assert 250 objects
- [x] 3.5 Run `bench/run.py` end-to-end and confirm `bench/report.pdf` includes the Rust service
