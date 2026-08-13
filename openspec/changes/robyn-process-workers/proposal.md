## Why

The existing Robyn benchmark (`robyn/`) starts the server with a single process and a single worker, which does not exercise Robyn's multi-process / multi-worker scaling capabilities. Adding a dedicated variant that exposes `processes` and `workers` as configurable startup variables lets the benchmark measure how Robyn behaves when it scales across CPU cores.

## What Changes

- Add a new `robyn-process-workers/` Python service variant.
- The new service copies the original `robyn/app.py` endpoint logic and passes `processes` and `workers` arguments to `app.start()`.
- The process and worker counts are read from environment variables (`ROBYN_PROCESSES` and `ROBYN_WORKERS`) with sensible defaults.
- Add a new port variable (`ROBYN_PROCESS_WORKERS_PORT`) to the shared `.env` file.
- Register the new service in `bench/run.py` so the benchmark harness can start and stop it alongside the other variants.
- Update `README.md` setup and run instructions to cover the new variant.

## Capabilities

### New Capabilities

- `rest-api-benchmark/robyn-process-workers`: A new Robyn service variant that accepts `processes` and `workers` startup configuration and exposes the same `GET /spatial_ref_sys` endpoint as the other benchmark services.

### Modified Capabilities

- `rest-api-benchmark`: Extend the benchmark harness and shared environment configuration to include the new Robyn process/workers variant and run it under the same load conditions as the other services.

## Impact

- New Python service directory with a `requirements.txt` and `app.py`.
- New `.env` entries for the additional service and its `processes` / `workers` tuning.
- `bench/run.py` gains a new `SERVICES` entry and `SERVICE_PORTS` mapping.
- `README.md` documentation is extended with setup and manual-run instructions.
- No breaking changes to existing services or the harness behavior.
