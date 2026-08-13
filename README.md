# REST API Performance Benchmark

This project compares six REST stacks on the same database-bound endpoint:

- **[FastAPI](https://fastapi.tiangolo.com) + [Uvicorn](https://www.uvicorn.org)** (`fastapi-uvicorn/`)
- **[FastAPI](https://fastapi.tiangolo.com) + [Granian](https://github.com/emmett-framework/granian)** (`fastapi-granian/`)
- **[Robyn](https://github.com/sansyrox/robyn)** (`robyn/`)
- **Robyn + multi-process/worker scaling** (`robyn-process-workers/`)
- **[Go Fiber](https://gofiber.io) + [`database/sql`](https://pkg.go.dev/database/sql) + [`lib/pq`](https://github.com/lib/pq)** (`go-fiber/`)
- **Rust + [Axum](https://github.com/tokio-rs/axum) + [`deadpool-postgres`](https://github.com/bikeshedder/deadpool)** (`rust-axum/`)

Each service exposes one endpoint, `GET /spatial_ref_sys`, that returns the first 100 rows of the PostgreSQL `spatial_ref_sys` table as a JSON array. The `bench/` harness starts each service, runs `wrk` with the same concurrency settings, and produces a `report.pdf`.

## What this benchmark measures

The goal is to compare how each framework handles the same real-world, database-bound HTTP workload:

- **HTTP/JSON stack**: request parsing, routing, JSON serialization, and response generation.
- **Database integration**: an async/cached connection pool, a parameterized `SELECT`, and row-to-JSON conversion.
- **Concurrency scaling**: throughput and latency are recorded at multiple `wrk` connection counts (default `200`, but configurable).

Each run is preceded by a **warm-up pass** so Postgres caches and connection pools are hot. The harness can also record **CPU and memory** usage while `wrk` runs.

Two endpoint modes are tested:

1. **`/spatial_ref_sys` (DB mode)** — queries `SELECT srid, auth_name, auth_srid, srtext, proj4text FROM spatial_ref_sys LIMIT 100` through the framework's database pool. This measures the full request lifecycle including DB I/O and serialization.
2. **`/spatial_ref_sys?static=1` (static mode)** — returns the same 100 rows from an in-memory cache loaded at startup. This removes Postgres from the path and isolates raw HTTP/JSON speed.

You can also stress JSON serialization by requesting `/spatial_ref_sys?limit=<n>` (clamped 1–1000) in DB mode to see how each framework scales the payload size.

## Requirements

- Python 3.12
- Go 1.26+
- Rust 1.70+ and `cargo`
- `uv` (recommended for Python virtualenvs) or `python3.12 -m venv`
- `wrk` installed and on `PATH`
- A reachable PostgreSQL server with the `spatial_ref_sys` table in a `public` schema

## Configure the environment

Copy `.env` from the repo root and set your database credentials and ports:

```env
DB_HOST=10.0.0.163
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=<your-password>
DB_NAME=postgres
DATABASE_URL=postgres://postgres:<your-password>@10.0.0.163:5432/postgres?sslmode=disable

FASTAPI_UVICORN_PORT=8001
FASTAPI_GRANIAN_PORT=8002
ROBYN_PORT=8003
GO_FIBER_PORT=8004
RUST_AXUM_PORT=8005
ROBYN_PROCESS_WORKERS_PORT=8006
ROBYN_PROCESSES=2
ROBYN_WORKERS=4
```

`.env` is gitignored by default.

## Setup

### Python services

Create a virtualenv in each Python project and install dependencies:

```bash
cd fastapi-uvicorn
uv venv --python 3.12 .venv
uv pip install -r requirements.txt --python .venv/bin/python
cd ..

cd fastapi-granian
uv venv --python 3.12 .venv
uv pip install -r requirements.txt --python .venv/bin/python
cd ..

cd robyn
uv venv --python 3.12 .venv
uv pip install -r requirements.txt --python .venv/bin/python
cd ..

# Robyn multi-process/workers variant
cd robyn-process-workers
uv venv --python 3.12 .venv
uv pip install -r requirements.txt --python .venv/bin/python
cd ..
```

### Go service

```bash
cd go-fiber
go build -o go-fiber
cd ..
```

### Rust service

```bash
cd rust-axum
cargo build --release
cd ..
```

### Benchmark harness

```bash
cd bench
uv venv --python 3.12 .venv
uv pip install -r requirements.txt --python .venv/bin/python
cd ..
```

## Run the benchmark

From the repository root:

```bash
cd bench
.venv/bin/python run.py
```

By default this runs the database-backed endpoint at 200 connections and writes `report.pdf`.

## Runner options

`bench/run.py` now supports several switches:

```bash
# Compare db and in-memory (static) modes
cd bench
.venv/bin/python run.py --mode db static

# Sweep concurrency
cd bench
.venv/bin/python run.py --concurrency 50 100 200 500

# Add a 5-second warm-up and record CPU / memory (default)
cd bench
.venv/bin/python run.py --warmup 5s --monitor

# Stress serialization with a larger payload
cd bench
.venv/bin/python run.py --limit 1000

# Run only one service
cd bench
.venv/bin/python run.py --services fastapi-uvicorn
```

The `static` mode (`/spatial_ref_sys?static=1`) returns the same 100 rows from a pre-loaded in-memory cache instead of querying the database, which lets you see the framework's raw HTTP/JSON speed without Postgres latency.

Common combinations:

```bash
# Default: db mode, c=200, 5s warm-up, report
cd bench
.venv/bin/python run.py

# Framework-only comparison at 200 connections
cd bench
.venv/bin/python run.py --mode static --concurrency 200

# DB scaling sweep with resource monitoring
cd bench
.venv/bin/python run.py --mode db --concurrency 50 100 200 500 --monitor

# Serialization stress at 1000 rows
cd bench
.venv/bin/python run.py --limit 1000 --concurrency 200
```

## Regenerate only the report

If you already have `wrk` output files in `bench/results/` and want to regenerate the PDF:

```bash
cd bench
.venv/bin/python report.py
```

## Run a service manually

Source the `.env` and start a single server for a quick `curl` test:

```bash
set -a && . .env && set +a

# FastAPI + Uvicorn
cd fastapi-uvicorn
.venv/bin/uvicorn main:app --host 0.0.0.0 --port $FASTAPI_UVICORN_PORT

# FastAPI + Granian
cd fastapi-granian
.venv/bin/granian --interface asgi main:app --host 0.0.0.0 --port $FASTAPI_GRANIAN_PORT

# Robyn
cd robyn
.venv/bin/python app.py

# Robyn multi-process/workers variant
cd robyn-process-workers
.venv/bin/python app.py

# Go Fiber
cd go-fiber
./go-fiber

# Rust + Axum
cd rust-axum
./target/release/rust-axum
```

## Expected response

All services return a 200 JSON array of 100 objects:

```json
[
  {
    "srid": 2000,
    "auth_name": "EPSG",
    "auth_srid": 2000,
    "srtext": "...",
    "proj4text": "..."
  },
  ...
]
```

You can request the in-memory cached version with `?static=1`:

```bash
curl 'http://127.0.0.1:8001/spatial_ref_sys?static=1' | jq '. | length'
```

## Notes

- The `.env` file is gitignored. Do not commit credentials.
- The `go-fiber` and `rust-axum` release binaries are gitignored.
- The query uses natural table order (`LIMIT 100`, no `ORDER BY`) as requested by the benchmark design.
- The `--limit` option only affects database-backed (`db`) mode; static mode always returns the cached 100 rows.
