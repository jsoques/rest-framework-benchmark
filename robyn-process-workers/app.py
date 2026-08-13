import os
from pathlib import Path

import asyncpg
from dotenv import load_dotenv
from pydantic import BaseModel
from robyn import Robyn

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

app = Robyn(__file__)

QUERY = (
    "SELECT srid, auth_name, auth_srid, srtext, proj4text "
    "FROM spatial_ref_sys LIMIT $1"
)


class SpatialRef(BaseModel):
    srid: int
    auth_name: str | None = None
    auth_srid: int | None = None
    srtext: str | None = None
    proj4text: str | None = None


def clamp_limit(value, default=100):
    if not value:
        return default
    try:
        n = int(value)
    except ValueError:
        return default
    return max(1, min(n, 1000))


pool = None
cached_records = None


@app.startup_handler
async def on_startup():
    global pool, cached_records
    pool = await asyncpg.create_pool(
        os.environ["DATABASE_URL"],
        min_size=5,
        max_size=50,
    )
    async with pool.acquire() as conn:
        rows = await conn.fetch(QUERY, 100)
    cached_records = [SpatialRef.model_validate(dict(r)).model_dump() for r in rows]


@app.shutdown_handler
async def on_shutdown():
    if pool:
        await pool.close()


@app.get("/spatial_ref_sys")
async def get_spatial_ref_sys(request):
    if request.query_params.get("static", None):
        return cached_records
    limit = clamp_limit(request.query_params.get("limit", None))
    async with pool.acquire() as conn:
        rows = await conn.fetch(QUERY, limit)
    records = [SpatialRef.model_validate(dict(r)).model_dump() for r in rows]
    return records


if __name__ == "__main__":
    app.config.processes = int(os.environ.get("ROBYN_PROCESSES", "1"))
    app.config.workers = int(os.environ.get("ROBYN_WORKERS", "1"))

    # Robyn's app.start() overrides the port argument with $ROBYN_PORT,
    # so ensure the environment matches the dedicated variant port.
    os.environ["ROBYN_PORT"] = os.environ["ROBYN_PROCESS_WORKERS_PORT"]

    print(
        f"Starting Robyn with {app.config.processes} processes "
        f"and {app.config.workers} workers"
    )

    app.start(host="0.0.0.0", port=int(os.environ["ROBYN_PROCESS_WORKERS_PORT"]))
