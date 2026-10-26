"""Application settings, overridable through environment variables."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

import pandas as pd
from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Runtime configuration for the API."""

    model_config = SettingsConfigDict(env_prefix="FORECAST_")

    data_dir: Path = BACKEND_DIR / "data"
    window_start: pd.Timestamp = pd.Timestamp("2026-01-01T00:00:00Z")
    window_end: pd.Timestamp = pd.Timestamp("2026-01-31T23:30:00Z")
    max_horizon_hours: int = 48
    default_horizon_hours: int = 4
    cors_origins: Annotated[list[str], NoDecode] = ["*"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_origins(cls, value: Any) -> Any:
        """Accept a JSON list, a comma-separated string or a single origin."""
        if not isinstance(value, str):
            return value
        value = value.strip()
        items = json.loads(value) if value.startswith("[") else value.split(",")
        # Browsers send origins without a trailing slash.
        return [item.strip().rstrip("/") for item in items if item.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings instance."""
    return Settings()
