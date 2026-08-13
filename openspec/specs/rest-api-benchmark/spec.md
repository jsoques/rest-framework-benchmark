## Purpose

Provides a common REST endpoint and benchmark harness so that FastAPI+Uvicorn, FastAPI+Granian, Robyn, and Go Fiber can be compared under identical load conditions.

## Requirements

### Requirement: Common endpoint across all services
Each service SHALL expose exactly one `GET /spatial_ref_sys` route on the port defined for that service.

#### Scenario: Endpoint is reachable
- **WHEN** a client sends a `GET` request to `http://<service-host>:<service-port>/spatial_ref_sys`
- **THEN** the service responds with HTTP status `200 OK`

### Requirement: Database query is identical
The endpoint SHALL execute `SELECT srid, auth_name, auth_srid, srtext, proj4text FROM spatial_ref_sys LIMIT 100` with no `ORDER BY` clause.

#### Scenario: Query returns 100 rows
- **WHEN** the `GET /spatial_ref_sys` endpoint is called
- **THEN** the response body contains a JSON array of exactly 100 objects representing the first 100 rows returned by the query

### Requirement: Response is a JSON array of objects
The endpoint SHALL return `Content-Type: application/json` and a top-level JSON array of objects, where each object contains the keys `srid`, `auth_name`, `auth_srid`, `srtext`, and `proj4text`.

#### Scenario: Response shape is correct
- **WHEN** the endpoint returns a successful response
- **THEN** each element in the array is an object whose keys match the selected columns and whose values are the row data or `null` where the column is null

### Requirement: Python services use Pydantic v2 for response models
The Python services SHALL define the response object with a Pydantic v2 `BaseModel` and use it to serialize the JSON output.

#### Scenario: Response is Pydantic-validated
- **WHEN** a Python service serializes a row
- **THEN** the output matches the Pydantic model and the endpoint returns it as JSON

### Requirement: Database connections are pooled
The Python services SHALL connect to PostgreSQL through `asyncpg.Pool`. The Go service SHALL use `database/sql` with `lib/pq` and configure `SetMaxOpenConns`. All services SHALL use the pool size defined in the design document.

#### Scenario: Concurrent requests share the pool
- **WHEN** 200 concurrent clients request the endpoint
- **THEN** each service uses its configured connection pool to serve the queries without opening a new connection per request

### Requirement: Configuration lives in a shared, gitignored `.env`
The database connection string and the per-service ports SHALL be read from a `.env` file in the repo root. The `.env` file SHALL be listed in `.gitignore` and the credentials SHALL NOT be committed to the repository.

#### Scenario: Service reads environment on startup
- **WHEN** a service starts
- **THEN** it reads the database host, port, user, password, database name, and its own listening port from the environment populated by the `.env` file

### Requirement: Benchmark harness uses fixed `wrk` parameters
The benchmark harness SHALL run `wrk -t8 -c200 -d30s -L --timeout 10s` against each service sequentially.

#### Scenario: wrk is invoked correctly
- **WHEN** the harness is executed
- **THEN** it runs `wrk` with 8 threads, 200 connections, a 30-second duration, the latency-distribution flag, and a 10-second timeout for each configured service URL

### Requirement: Benchmark harness produces a PDF report
The harness SHALL generate a `report.pdf` containing a summary table and bar charts comparing each service's throughput (`Requests/sec`) and `99%` latency.

#### Scenario: PDF is generated after the benchmark
- **WHEN** all `wrk` runs complete
- **THEN** a `report.pdf` file exists in the `bench/` directory with a results table and charts for throughput and p99 latency
