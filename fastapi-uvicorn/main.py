import os
from contextlib import asynccontextmanager
from pathlib import Path

import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from pydantic import BaseModel

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

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


def clamp_limit(value: str | None, default: int = 100) -> int:
    if not value:
        return default
    try:
        n = int(value)
    except ValueError:
        return default
    return max(1, min(n, 1000))


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(
        os.environ["DATABASE_URL"],
        min_size=5,
        max_size=50,
    )
    async with app.state.pool.acquire() as conn:
        rows = await conn.fetch(QUERY, 100)
    app.state.cached_records = [dict(r) for r in rows]
    yield
    await app.state.pool.close()


app = FastAPI(lifespan=lifespan)


@app.get("/spatial_ref_sys", response_model=list[SpatialRef])
async def get_spatial_ref_sys(request: Request):
    if request.query_params.get("static"):
        return request.app.state.cached_records
    limit = clamp_limit(request.query_params.get("limit"))
    async with request.app.state.pool.acquire() as conn:
        rows = await conn.fetch(QUERY, limit)
    return [dict(r) for r in rows]
