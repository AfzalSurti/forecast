"""Load the cached Elexon datasets from ``backend/data``."""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from app.config import get_settings


@lru_cache
def load_actuals() -> pd.DataFrame:
    """Return half-hourly wind outturn: ``start_time`` (UTC), ``generation_mw``."""
    df = pd.read_csv(get_settings().data_dir / "actuals.csv")
    df["start_time"] = pd.to_datetime(df["start_time"], utc=True)
    return df.sort_values("start_time").reset_index(drop=True)


@lru_cache
def load_forecasts() -> pd.DataFrame:
    """Return WINDFOR forecasts: ``start_time``, ``publish_time`` (UTC), ``generation_mw``."""
    df = pd.read_csv(get_settings().data_dir / "forecasts.csv")
    df["start_time"] = pd.to_datetime(df["start_time"], utc=True)
    df["publish_time"] = pd.to_datetime(df["publish_time"], utc=True)
    return df.sort_values(["start_time", "publish_time"]).reset_index(drop=True)
