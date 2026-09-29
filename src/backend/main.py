"""CASHNET Backend Application Entry Point."""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.backend.api.router import api_router
from src.backend.api.routes import health
from src.backend.config import settings
from src.backend.db.base import Base
from src.backend.db.session import engine
import src.backend.db.models  # Ensure all models are registered with Base metadata

logger = logging.getLogger("cashnet.backend")


def _init_db_schema() -> None:
    """Safely initialize schema tables if database permits DDL."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning("Database schema auto-creation note: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown routines."""
    _init_db_schema()
    yield
    # Shutdown: cleanup


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    _init_db_schema()
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description=(
            "AI-assisted cybercrime cash-out prediction and investigator decision-support platform.\n\n"
            "**SIMULATION / PROTOTYPE DISCLAIMER:** All case records, account histories, financial transactions, "
            "and geospatial coordinates are synthetically generated for research, prototype development, "
            "and tactical evaluation."
        ),
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # Root-level health check endpoint
    app.include_router(health.router)

    # API v1 versioned endpoints
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Mount static assets and serve Investigator Dashboard at root /
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

        @app.get("/", include_in_schema=False)
        async def serve_dashboard():
            return FileResponse(os.path.join(static_dir, "index.html"))

        @app.get("/dashboard", include_in_schema=False)
        async def serve_dashboard_alias():
            return FileResponse(os.path.join(static_dir, "index.html"))

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.backend.main:app", host="0.0.0.0", port=8000, reload=True)
