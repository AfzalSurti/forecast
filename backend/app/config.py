"""Application settings, overridable through environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Runtime configuration for the API."""

    model_config = SettingsConfigDict(env_prefix="FORECAST_")

    data_dir: Path = BACKEND_DIR / "data"
    window_start: pd.Timestamp = pd.Timestamp("2026-01-01T00:00:00Z")
    window_end: pd.Timestamp = pd.Timestamp("2026-01-31T23:30:00Z")
    max_horizon_hours: int = 48
    default_horizon_hours: int = 4
    cors_origins: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings instance."""
    return Settings()
