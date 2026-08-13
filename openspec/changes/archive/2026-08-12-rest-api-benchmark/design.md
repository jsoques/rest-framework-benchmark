## Context

The repo is greenfield scaffolding with no existing source code or build tooling. This change introduces four independent REST servers and a benchmark harness to compare them under identical conditions. See `proposal.md` for the motivation and `specs/rest-api-benchmark/spec.md` for the behavioral contract.

## Goals / Non-Goals

**Goals:**
- Provide a single `GET /spatial_ref_sys` endpoint in FastAPI+Uvicorn, FastAPI+Granian, Robyn, and Go Fiber.
- Keep the query, response shape, and database connection strategy as similar as possible across all four stacks.
- Run a reproducible `wrk` load test and produce a `report.pdf` with throughput and p99 latency charts.
- Keep credentials out of the repository.

**Non-Goals:**
- General application features (health checks, logging, authentication, multiple endpoints).
- Tuning the database server or the query beyond the required `LIMIT 100`.
- Cross-framework error-handling comparisons or stress tests beyond the single endpoint.

## Decisions

### Python server choice: FastAPI + Uvicorn / Granian / Robyn
- **Rationale:** The benchmark explicitly targets FastAPI on Uvicorn, FastAPI on Granian, and Robyn. FastAPI with Uvicorn is the reference ASGI stack; Granian is a Rust-based ASGI/WSGI server; Robyn is a Rust-core Python framework with a different concurrency model.
- **Alternatives considered:** Running only Uvicorn and comparing workers (`--workers`), but the user requested Granian and Robyn as separate projects.

### Python database driver: `asyncpg`
- **Rationale:** `asyncpg` is the fastest PostgreSQL driver for the async Python frameworks and is natively compatible with FastAPI and Robyn async handlers.
- **Alternatives considered:** `psycopg` (slower for this workload) and raw `psycopg2` (synchronous, not a fair comparison for async servers).

### Go database driver: `lib/pq` through `database/sql`
- **Rationale:** The user explicitly requested `database/sql`. `lib/pq` is the established `database/sql` driver for PostgreSQL.
- **Alternatives considered:** `pgx/stdlib` (also works with `database/sql` and is faster), but the explicit instruction is `database/sql`, so `lib/pq` is the default choice.

### Connection pool size: `max_size=50` (Python) / `SetMaxOpenConns(50)` (Go)
- **Rationale:** The `wrk` concurrency is 200 HTTP connections, but the query is short. A 50-connection DB pool keeps each service well under a default Postgres `max_connections=100` while still avoiding per-request connection creation. Pool size is the same across services to make the comparison fair.
- **Alternatives considered:** `max_size=200` (could exhaust Postgres) and `max_size=10` (could serialize DB access and mask framework differences).

### Query: no `ORDER BY`
- **Rationale:** The user explicitly requested the natural order and first 100 rows with no `ORDER BY`. This is deterministic enough for a catalog table (`spatial_ref_sys`) in a single benchmark run.
- **Trade-off:** Rows may not be sorted; JSON arrays may differ between runs if the planner changes, but the shape and count are fixed.

### Benchmark tool: `wrk` with `-L`
- **Rationale:** `wrk` is already installed on the target machine, the requested concurrency maps directly to `wrk -t8 -c200 -d30s`, and `-L` prints percentile distribution (50%, 75%, 90%, 99%).
- **Alternatives considered:** `k6` (better JSON output, not installed), a Python `aiohttp` client (simpler for PDF parsing, risk of client-side bottleneck), `oha` (not installed).

### PDF generation: `matplotlib` + `fpdf2`
- **Rationale:** `matplotlib` generates the bar charts, and `fpdf2` is a pure-Python PDF writer that can embed those charts and build a results table with little overhead.
- **Alternatives considered:** `reportlab` (heavier dependency, more complex API) and `weasyprint` (requires system libraries).

### Ports and environment
- Ports are assigned per service via the `.env` file:
  - `FASTAPI_UVICORN_PORT=8001`
  - `FASTAPI_GRANIAN_PORT=8002`
  - `ROBYN_PORT=8003`
  - `GO_FIBER_PORT=8004`
- `DATABASE_URL=postgres://postgres:<password>@10.0.0.163:5432/postgres` (or split into `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` for Python).

## Risks / Trade-offs

- **Python 3.14.3 package availability** → `asyncpg`, `pydantic`, `robyn`, `granian`, `matplotlib`, and `fpdf2` may not have wheels for Python 3.14. If they do not install cleanly, the implementation may need to use an older Python version via `pyenv` or `uv`.
- **Database network latency dominates small differences** → The DB is on the same network but not the same host. If round-trip time to `10.0.0.163` is high, the numbers will reflect DB+network time more than framework differences.
- **`wrk` text parsing is brittle** → `wrk` does not output JSON. The report parser must be maintained with `wrk`'s exact text format. If `wrk` is upgraded or the locale changes, parsing could break.
- **Robyn asyncpg pool lifecycle** → Robyn's startup/shutdown hooks are less mature than FastAPI's. We may need to open the pool at import time and rely on process lifetime for cleanup.
- **Credentials in `.env`** → While gitignored, the `.env` still lives on disk. The benchmark is local and throwaway, but users should not share the directory.
- **`lib/pq` maintenance status** → `lib/pq` is in maintenance mode; for production `pgx` is preferred, but it is still the standard `database/sql` driver and is sufficient for this benchmark.

## Migration Plan

No migration is required. The change is additive. Deployment steps are:
1. Create the four project directories and `bench/`.
2. Set the shared `.env` with the database credentials and ports.
3. Install each Python project's `.venv` and Go module.
4. Start each service individually, run `wrk`, and then run the report generator.

## Open Questions

None at this stage; all technical choices that affect the spec or task breakdown have been resolved with the user.
