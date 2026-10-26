"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import data, metrics


def create_app() -> FastAPI:
    """Build the API application."""
    app = FastAPI(
        title="UK Wind Forecast Monitor",
        description="Elexon BMRS national wind forecasts vs actuals, January 2026.",
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(data.router)
    app.include_router(metrics.router)
    return app


app = create_app()
