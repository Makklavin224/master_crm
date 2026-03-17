from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1.router import api_v1_router
from app.core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify DB connection
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    yield
    # Shutdown: dispose engine
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Master CRM API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(api_v1_router, prefix="/api/v1")
    return app


app = create_app()
