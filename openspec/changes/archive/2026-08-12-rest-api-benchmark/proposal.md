## Why

The project needs comparable, repeatable throughput and latency measurements for a realistic database-bound REST workload across the four stacks it is intended to evaluate. Running each server with the same endpoint, the same query, and the same `wrk` load generator will produce a fair, reproducible comparison of FastAPI+Uvicorn, FastAPI+Granian, Robyn, and Go Fiber.

## What Changes

- Add four independent server projects under the repo root, one for each target framework:
  - `fastapi-uvicorn/`: FastAPI served by Uvicorn
  - `fastapi-granian/`: FastAPI served by Granian
  - `robyn/`: Robyn framework
  - `go-fiber/`: Go Fiber with `database/sql` + `lib/pq`
- Add a single `GET /spatial_ref_sys` endpoint to each server that returns the first 100 rows of the `spatial_ref_sys` PostgreSQL table as a JSON array of objects.
- Add a `bench/` harness that runs `wrk -t8 -c200 -d30s -L` against each server and produces `report.pdf` with throughput and latency charts.
- Add a shared, gitignored `.env` file for database connection and ports.
- Add per-project dependency files (`requirements.txt` / `go.mod`) and build/launch instructions.

## Capabilities

### New Capabilities
- `rest-api-benchmark`: Four single-endpoint REST services and a benchmark harness compare FastAPI+Uvicorn, FastAPI+Granian, Robyn, and Go Fiber against the same PostgreSQL query, producing a PDF report of throughput and latency.

### Modified Capabilities
- None (this is a greenfield benchmark; no existing behavior is changing).

## Impact

- New Python virtualenvs and Go module for dependencies; requires `wrk`, PostgreSQL connectivity to `10.0.0.163`, and packages such as `asyncpg`, `pydantic`, `robyn`, `granian`, `lib/pq`, `matplotlib`, and `fpdf2`.
- The PostgreSQL server will be loaded sequentially, one service at a time, with 200 concurrent `wrk` connections for 30 seconds each.
- Credentials live only in the gitignored `.env` file; they are not committed.
