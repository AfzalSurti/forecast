"""Time-series endpoints: health, actuals, forecasts and comparison."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.config import get_settings
from app.dependencies import HorizonParam, Window, to_records, window_params
from app.schemas import ActualPoint, ComparisonPoint, ForecastPoint, HealthResponse
from app.services.analysis import comparison, filter_window, selected_forecasts
from app.services.data_loader import load_actuals, load_forecasts

router = APIRouter(prefix="/api", tags=["data"])
WindowDep = Annotated[Window, Depends(window_params)]


@router.get("/health", response_model=HealthResponse)
def health() -> dict:
    """Report service status and the size of the cached datasets."""
    settings = get_settings()
    return {
        "status": "ok",
        "actual_rows": len(load_actuals()),
        "forecast_rows": len(load_forecasts()),
        "window_start": settings.window_start,
        "window_end": settings.window_end,
    }


@router.get("/actuals", response_model=list[ActualPoint])
def actuals(window: WindowDep) -> list[dict]:
    """Half-hourly actual wind generation in the window."""
    return to_records(filter_window(load_actuals(), window.start, window.end))


@router.get("/forecasts", response_model=list[ForecastPoint])
def forecasts(window: WindowDep, horizon: HorizonParam = 4) -> list[dict]:
    """Forecast series for the window, using the forecast selected at ``horizon``."""
    return to_records(filter_window(selected_forecasts(horizon), window.start, window.end))


@router.get("/comparison", response_model=list[ComparisonPoint])
def comparison_series(window: WindowDep, horizon: HorizonParam = 4) -> list[dict]:
    """Aligned actual, forecast and error per forecast target slot."""
    return to_records(filter_window(comparison(horizon), window.start, window.end))
