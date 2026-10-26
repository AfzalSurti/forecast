"""Forecast accuracy endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import HorizonParam, Window, window_params
from app.schemas import HorizonMetrics, HourMetrics, MetricsResponse
from app.services.analysis import comparison, filter_window
from app.services.metrics import compute_metrics, metrics_by_hour

router = APIRouter(prefix="/api/metrics", tags=["metrics"])
WindowDep = Annotated[Window, Depends(window_params)]


@router.get("", response_model=MetricsResponse)
def metrics(window: WindowDep, horizon: HorizonParam = 4) -> dict:
    """Error statistics for one horizon over the window."""
    stats = compute_metrics(filter_window(comparison(horizon), window.start, window.end))
    return {"horizon_hours": horizon, "start": window.start, "end": window.end, **stats}


@router.get("/by-horizon", response_model=list[HorizonMetrics])
def metrics_by_horizon(
    window: WindowDep,
    step: Annotated[float, Query(gt=0, le=48, description="Horizon step in hours")] = 1,
) -> list[dict]:
    """MAE, RMSE and bias for horizons 0..48 hours in ``step`` increments."""
    rows = []
    horizon = 0.0
    while horizon <= 48:
        stats = compute_metrics(filter_window(comparison(horizon), window.start, window.end))
        rows.append(
            {
                "horizon_hours": horizon,
                "n_forecasts": stats["n_forecasts"],
                "coverage_pct": stats["coverage_pct"],
                "mae": stats["mae"],
                "rmse": stats["rmse"],
                "bias": stats["bias"],
                "p90_abs_error": stats["abs_error_percentiles"]["p90"],
            }
        )
        horizon += step
    return rows


@router.get("/by-hour", response_model=list[HourMetrics])
def metrics_by_hour_of_day(window: WindowDep, horizon: HorizonParam = 4) -> list[dict]:
    """Error statistics grouped by UTC hour of day."""
    return metrics_by_hour(filter_window(comparison(horizon), window.start, window.end))
