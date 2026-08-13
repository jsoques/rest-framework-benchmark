## Context

See `proposal.md` for the motivation. The existing `robyn/` service reuses the standard `app.start(host, port)` call and therefore runs with a single process and a single worker, which under-represents Robyn's multi-process scaling. The new variant must expose the same endpoint behavior while allowing `processes` and `workers` to be tuned.

## Goals / Non-Goals

**Goals:**
- Add a new `robyn-process-workers/` service that is a drop-in replacement for `robyn/` for the benchmark.
- Make `processes` and `workers` externally configurable through environment variables.
- Wire the new service into the existing `.env` and benchmark harness without changing the harness contract.

**Non-Goals:**
- Modifying the original `robyn/` service.
- Changing the database schema, query, or response shape.
- Automating the selection of optimal `processes`/`workers` values.

## Decisions

### 1. Set `app.config.processes` and `app.config.workers` before `app.start()`
**Rationale:** Robyn's `Robyn.start()` signature does not expose `processes` or `workers` parameters, but it reads `self.config.processes` and `self.config.workers` when spawning the Rust runtime. Setting those attributes on the `app.config` object before `app.start()` lets us source the values from the environment.
**Alternative considered:** Passing `--processes` and `--workers` as CLI flags to `python app.py`. Rejected because the benchmark harness already manages the start command from `SERVICES`, and the environment-variable approach keeps the configuration consolidated in `.env` alongside the other service ports.

### 2. Create a new `robyn-process-workers/` directory instead of editing `robyn/`
**Rationale:** A separate variant lets users compare the baseline single-process Robyn with the multi-process version directly in the same benchmark run without switching branches or re-running setup.
**Alternative considered:** Add the logic to `robyn/` with conditional multi-process behavior. Rejected because it would change the baseline measurements and complicate the existing service.

### 3. Read `ROBYN_PROCESSES`, `ROBYN_WORKERS`, and `ROBYN_PROCESS_WORKERS_PORT` from `.env`
**Rationale:** The project already uses a shared `.env` for all service ports and database credentials. Adding the new port and tuning variables there follows the existing convention.

### 4. Copy the endpoint logic from `robyn/app.py` unchanged
**Rationale:** The variant only differs in startup scaling, not endpoint behavior. Copying the existing `app.py` keeps the two services aligned and reduces the chance of behavioral drift.

## Risks / Trade-offs

- **Risk:** `app.config` is an internal `Config` object. Setting `processes` and `workers` attributes after instantiation is not a documented public API, so it could break on a future Robyn version.
  - **Mitigation:** Pin the same `robyn` version in `requirements.txt` and add a startup validation that the values were accepted.
- **Risk:** Running multiple Robyn processes multiplies the `asyncpg` pool footprint because each process creates its own pool.
  - **Mitigation:** Keep the same `min_size`/`max_size` as the baseline and document that this is the intended cost of multi-process scaling.
- **Risk:** The `ROBYN_PROCESSES` and `ROBYN_WORKERS` environment variables are not part of Robyn's built-in configuration, so they are only meaningful for this wrapper.
  - **Mitigation:** Use a clear `ROBYN_` prefix and default to `1` when unset so the service still starts without them.

## Open Questions

None.
