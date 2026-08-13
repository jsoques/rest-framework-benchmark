## ADDED Requirements

### Requirement: Benchmark harness includes the Robyn process/workers variant
The benchmark harness SHALL start, warm, and run `wrk` against the `robyn-process-workers` service when the default or explicit service list is used.

#### Scenario: Default run includes the new variant
- **WHEN** `bench/run.py` is executed with default parameters
- **THEN** the harness starts `robyn-process-workers`, runs the configured `wrk` load, and stores the results in `bench/results/`

#### Scenario: Service can be selected explicitly
- **WHEN** `bench/run.py --services robyn-process-workers` is executed
- **THEN** the harness benchmarks only the `robyn-process-workers` service

### Requirement: Shared `.env` defines the new service port
The shared `.env` file SHALL include a `ROBYN_PROCESS_WORKERS_PORT` entry, and the benchmark harness and service SHALL read the port from the environment.

#### Scenario: Port is available to the harness
- **WHEN** the environment is loaded from the shared `.env` file
- **THEN** `ROBYN_PROCESS_WORKERS_PORT` is populated and the harness uses it to build the `robyn-process-workers` URL
