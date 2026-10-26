"""Shared request parameters and serialisation helpers for the routers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

import pandas as pd
from fastapi import HTTPException, Query

from app.config import get_settings


@dataclass(frozen=True)
class Window:
    """Validated UTC time window for a request."""

    start: pd.Timestamp
    end: pd.Timestamp


def _to_utc(value: datetime) -> pd.Timestamp:
    """Interpret naive datetimes as UTC and convert aware ones to UTC."""
    ts = pd.Timestamp(value)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def window_params(
    start: Annotated[datetime | None, Query(description="Window start (UTC, ISO 8601)")] = None,
    end: Annotated[datetime | None, Query(description="Window end (UTC, ISO 8601)")] = None,
) -> Window:
    """Parse ``start``/``end``, defaulting to and clamping within the data window."""
    settings = get_settings()
    lo = max(_to_utc(start), settings.window_start) if start else settings.window_start
    hi = min(_to_utc(end), settings.window_end) if end else settings.window_end
    if lo > hi:
        raise HTTPException(
            status_code=422, detail="start must be before end and within the data window"
        )
    return Window(start=lo, end=hi)


HorizonParam = Annotated[
    float,
    Query(ge=0, le=48, description="Forecast horizon in hours (0-48)"),
]


def to_records(df: pd.DataFrame) -> list[dict]:
    """Convert a frame to JSON-friendly dicts with ``None`` for NaN/NaT."""
    out = df.astype(object).where(df.notna(), None)
    return out.to_dict(orient="records")
