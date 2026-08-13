## Purpose

Provides a Robyn benchmark service variant that exposes the same `GET /spatial_ref_sys` endpoint as the other services while allowing the number of Robyn processes and workers to be configured at startup.

## ADDED Requirements

### Requirement: Project structure for the new variant
The system SHALL provide a `robyn-process-workers/` directory containing an `app.py` and a `requirements.txt` with the same Python dependencies as the existing `robyn/` service.

#### Scenario: Variant project exists
- **WHEN** the repository is cloned and the service directory is inspected
- **THEN** a `robyn-process-workers/` directory exists that contains `app.py` and `requirements.txt`

### Requirement: Endpoint matches the existing benchmark contract
The system SHALL expose `GET /spatial_ref_sys` on the configured port and return a JSON array of spatial reference records, supporting `?static=1` to return the in-memory cache and `?limit=<n>` to request a clamped row count.

#### Scenario: Database-backed request
- **WHEN** a client sends `GET /spatial_ref_sys` to the new service
- **THEN** the response is a JSON array of up to 100 row objects containing `srid`, `auth_name`, `auth_srid`, `srtext`, and `proj4text`

#### Scenario: Static cached request
- **WHEN** a client sends `GET /spatial_ref_sys?static=1`
- **THEN** the response is the JSON array of 100 rows that was loaded into memory at startup

#### Scenario: Custom limit request
- **WHEN** a client sends `GET /spatial_ref_sys?limit=50`
- **THEN** the response is a JSON array of exactly 50 row objects

### Requirement: Process and worker counts are configurable at startup
The system SHALL read `ROBYN_PROCESSES` and `ROBYN_WORKERS` from the environment and use those values when the application starts.

#### Scenario: Default counts
- **WHEN** the service starts without `ROBYN_PROCESSES` or `ROBYN_WORKERS` set
- **THEN** it starts with one process and one worker

#### Scenario: Explicit counts
- **WHEN** the service starts with `ROBYN_PROCESSES=2` and `ROBYN_WORKERS=4`
- **THEN** it runs two Robyn processes, each with four workers

### Requirement: Service listens on a dedicated port
The system SHALL read `ROBYN_PROCESS_WORKERS_PORT` from the environment and bind the HTTP listener to that port on `0.0.0.0`.

#### Scenario: Port is read from `.env`
- **WHEN** the environment contains `ROBYN_PROCESS_WORKERS_PORT=8006`
- **THEN** the service listens on `0.0.0.0:8006`
