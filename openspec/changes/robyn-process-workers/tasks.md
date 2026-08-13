## 1. Add the new Robyn process/workers variant

- [x] 1.1 Create the `robyn-process-workers/` directory and add a `requirements.txt` with the same dependencies as `robyn/requirements.txt`
- [x] 1.2 Create `robyn-process-workers/app.py` that reuses the existing endpoint logic and sets `app.config.processes` and `app.config.workers` from environment variables before calling `app.start()`

## 2. Add environment configuration

- [x] 2.1 Add `ROBYN_PROCESS_WORKERS_PORT`, `ROBYN_PROCESSES`, and `ROBYN_WORKERS` to the shared `.env` file
- [x] 2.2 Update `.gitignore` if necessary to keep the `.env` file excluded

## 3. Integrate the variant into the benchmark harness

- [x] 3.1 Add `robyn-process-workers` to `SERVICE_PORTS` in `bench/run.py` using `ROBYN_PROCESS_WORKERS_PORT`
- [x] 3.2 Add a `robyn-process-workers` entry to `SERVICES` in `bench/run.py` with the correct virtualenv and startup command

## 4. Update documentation

- [x] 4.1 Add the `robyn-process-workers` variant to the list of compared stacks in `README.md`
- [x] 4.2 Add setup and manual-run instructions for `robyn-process-workers` in `README.md`

## 5. Verify the implementation

- [x] 5.1 Install the new virtualenv and start the service manually, then confirm `GET /spatial_ref_sys` returns a 200 JSON array
- [x] 5.2 Run `bench/run.py --services robyn-process-workers --skip-report` and confirm `wrk` output is written to `bench/results/robyn-process-workers_db_c200.txt`
