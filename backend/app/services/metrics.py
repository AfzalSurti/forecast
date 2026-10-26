"""Forecast accuracy metrics.

Error is defined as ``forecast - actual``: positive values mean the forecast
over-estimated wind generation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PERCENTILES = (10, 50, 90, 95)


def build_comparison(actuals: pd.DataFrame, selected: pd.DataFrame) -> pd.DataFrame:
    """Align actual outturn with horizon-selected forecasts on ``start_time``.

    Only target slots present in ``selected`` (the forecast grid) are kept, so
    a slot with a missing forecast stays in the frame and counts against
    coverage.

    Returns:
        Columns ``start_time``, ``actual_mw``, ``forecast_mw``,
        ``publish_time``, ``lead_hours`` and ``error_mw``.
    """
    merged = selected.merge(
        actuals.rename(columns={"generation_mw": "actual_mw"}),
        on="start_time",
        how="inner",
    ).rename(columns={"generation_mw": "forecast_mw"})
    merged["error_mw"] = merged["forecast_mw"] - merged["actual_mw"]
    cols = ["start_time", "actual_mw", "forecast_mw", "publish_time", "lead_hours", "error_mw"]
    return merged[cols].sort_values("start_time").reset_index(drop=True)


def _percentiles(values: np.ndarray) -> dict[str, float | None]:
    """Return ``{"p10": ..., ...}`` or ``None`` values when ``values`` is empty."""
    if values.size == 0:
        return {f"p{p}": None for p in PERCENTILES}
    return {
        f"p{p}": float(v)
        for p, v in zip(PERCENTILES, np.percentile(values, PERCENTILES), strict=True)
    }


def compute_metrics(comparison: pd.DataFrame) -> dict:
    """Summarise forecast error over the rows of ``comparison``.

    Slots without a forecast are excluded from error statistics but counted
    in ``coverage_pct``.
    """
    total = len(comparison)
    valid = comparison.dropna(subset=["forecast_mw", "actual_mw"])
    n = len(valid)
    coverage = 100.0 * n / total if total else 0.0

    if n == 0:
        return {
            "n_slots": total,
            "n_forecasts": 0,
            "coverage_pct": coverage,
            "mae": None,
            "rmse": None,
            "bias": None,
            "mape": None,
            "nmae_pct": None,
            "mean_actual": None,
            "error_percentiles": _percentiles(np.array([])),
            "abs_error_percentiles": _percentiles(np.array([])),
        }

    err = valid["error_mw"].to_numpy(dtype=float)
    actual = valid["actual_mw"].to_numpy(dtype=float)
    abs_err = np.abs(err)
    nonzero = actual != 0
    mean_actual = float(actual.mean())
    mae = float(abs_err.mean())
    return {
        "n_slots": total,
        "n_forecasts": n,
        "coverage_pct": coverage,
        "mae": mae,
        "rmse": float(np.sqrt(np.mean(err**2))),
        "bias": float(err.mean()),
        "mape": (
            float(100.0 * np.mean(abs_err[nonzero] / actual[nonzero])) if nonzero.any() else None
        ),
        "nmae_pct": 100.0 * mae / mean_actual if mean_actual else None,
        "mean_actual": mean_actual,
        "error_percentiles": _percentiles(err),
        "abs_error_percentiles": _percentiles(abs_err),
    }


def metrics_by_hour(comparison: pd.DataFrame) -> list[dict]:
    """Return MAE, RMSE, bias and count per UTC hour of day (0-23)."""
    valid = comparison.dropna(subset=["forecast_mw", "actual_mw"])
    rows = []
    for hour in range(24):
        err = valid.loc[valid["start_time"].dt.hour == hour, "error_mw"].to_numpy(dtype=float)
        rows.append(
            {
                "hour": hour,
                "n": int(err.size),
                "mae": float(np.abs(err).mean()) if err.size else None,
                "rmse": float(np.sqrt(np.mean(err**2))) if err.size else None,
                "bias": float(err.mean()) if err.size else None,
            }
        )
    return rows
