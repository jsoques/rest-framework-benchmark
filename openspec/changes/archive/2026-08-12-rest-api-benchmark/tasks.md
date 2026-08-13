## 1. Shared environment and configuration

- [x] 1.1 Create `.gitignore` to exclude `.env`, `.venv/`, `__pycache__/`, `.mypy_cache/`, `*.pyc`, `go-fiber/go-fiber`, and `bench/report.pdf`
- [x] 1.2 Create the root `.env` file with `DATABASE_URL`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, and the four service ports
- [x] 1.3 Verify PostgreSQL connectivity to `10.0.0.163` from the workspace before starting implementation

## 2. FastAPI + Uvicorn project

- [x] 2.1 Create `fastapi-uvicorn/main.py` with the `GET /spatial_ref_sys` endpoint, Pydantic v2 response model, and `asyncpg.Pool`
- [x] 2.2 Create `fastapi-uvicorn/requirements.txt` with FastAPI, Uvicorn, `asyncpg`, `pydantic`, and `python-dotenv`
- [x] 2.3 Create `fastapi-uvicorn/.venv`, install dependencies, and verify the endpoint returns 100 objects on port 8001

## 3. FastAPI + Granian project

- [x] 3.1 Create `fastapi-granian/main.py` with the same endpoint, Pydantic v2 response model, and `asyncpg.Pool`
- [x] 3.2 Create `fastapi-granian/requirements.txt` with FastAPI, Granian, `asyncpg`, `pydantic`, and `python-dotenv`
- [x] 3.3 Create `fastapi-granian/.venv`, install dependencies, and verify the endpoint returns 100 objects on port 8002

## 4. Robyn project

- [x] 4.1 Create `robyn/app.py` with the `GET /spatial_ref_sys` endpoint, Pydantic v2 response model, and `asyncpg.Pool`
- [x] 4.2 Create `robyn/requirements.txt` with `robyn`, `asyncpg`, `pydantic`, and `python-dotenv`
- [x] 4.3 Create `robyn/.venv`, install dependencies, and verify the endpoint returns 100 objects on port 8003

## 5. Go Fiber project

- [x] 5.1 Create `go-fiber/main.go` with the `GET /spatial_ref_sys` endpoint, `database/sql` + `lib/pq`, connection pool settings, and a results struct
- [x] 5.2 Initialize `go-fiber/go.mod`, add `github.com/gofiber/fiber/v2` and `github.com/lib/pq` dependencies, and build the binary
- [x] 5.3 Start the Go Fiber service and verify the endpoint returns 100 objects on port 8004

## 6. Benchmark harness and reporting

- [x] 6.1 Create `bench/run.py` to start each service, wait for readiness, run `wrk -t8 -c200 -d30s -L --timeout 10s`, and capture output to `bench/results/`
- [x] 6.2 Create `bench/report.py` to parse `wrk` output, build a results table, and generate throughput and p99 latency bar charts with `matplotlib` and `fpdf2`
- [x] 6.3 Create `bench/requirements.txt` with `matplotlib`, `fpdf2`, `python-dotenv`, and `psutil` (or similar process control)
- [x] 6.4 Run the full benchmark end-to-end and confirm `bench/report.pdf` is produced

## 7. Verification and cleanup

- [x] 7.1 `curl` each service and assert the response is a 200 JSON array of 100 objects with the expected keys
- [x] 7.2 Confirm `wrk` output contains `Requests/sec`, `Latency Distribution`, and 50/75/90/99 percentiles for every service
- [x] 7.3 Ensure no credentials are committed by running `git check-ignore .env` and `git status --short`
