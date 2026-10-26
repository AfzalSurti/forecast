"""Dataset-level helpers that combine loading, horizon selection and windowing."""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from app.services.data_loader import load_actuals, load_forecasts
from app.services.horizon import select_forecasts
from app.services.metrics import build_comparison


def filter_window(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Return rows whose ``start_time`` lies in ``[start, end]`` (inclusive)."""
    mask = (df["start_time"] >= start) & (df["start_time"] <= end)
    return df.loc[mask].reset_index(drop=True)


@lru_cache(maxsize=128)
def selected_forecasts(horizon_hours: float) -> pd.DataFrame:
    """Horizon-selected forecasts for every target slot in the cached data."""
    return select_forecasts(load_forecasts(), horizon_hours)


@lru_cache(maxsize=128)
def comparison(horizon_hours: float) -> pd.DataFrame:
    """Actual vs horizon-selected forecast for every forecast target slot."""
    return build_comparison(load_actuals(), selected_forecasts(horizon_hours))
