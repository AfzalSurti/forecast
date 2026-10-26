"""Pydantic response models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    actual_rows: int
    forecast_rows: int
    window_start: datetime
    window_end: datetime


class ActualPoint(BaseModel):
    start_time: datetime
    generation_mw: float


class ForecastPoint(BaseModel):
    start_time: datetime
    publish_time: datetime | None
    lead_hours: float | None
    generation_mw: float | None


class ComparisonPoint(BaseModel):
    start_time: datetime
    actual_mw: float | None
    forecast_mw: float | None
    publish_time: datetime | None
    lead_hours: float | None
    error_mw: float | None


class Percentiles(BaseModel):
    p10: float | None
    p50: float | None
    p90: float | None
    p95: float | None


class MetricsResponse(BaseModel):
    horizon_hours: float
    start: datetime
    end: datetime
    n_slots: int = Field(description="Forecast target slots in the window")
    n_forecasts: int = Field(description="Slots with a qualifying forecast")
    coverage_pct: float
    mae: float | None
    rmse: float | None
    bias: float | None = Field(description="Mean of forecast - actual (MW)")
    mape: float | None
    nmae_pct: float | None = Field(description="MAE as % of mean actual generation")
    mean_actual: float | None
    error_percentiles: Percentiles
    abs_error_percentiles: Percentiles


class HorizonMetrics(BaseModel):
    horizon_hours: float
    n_forecasts: int
    coverage_pct: float
    mae: float | None
    rmse: float | None
    bias: float | None
    p90_abs_error: float | None


class HourMetrics(BaseModel):
    hour: int
    n: int
    mae: float | None
    rmse: float | None
    bias: float | None
