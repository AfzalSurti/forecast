"""Tests for accuracy metrics."""

import math

import pandas as pd
import pytest

from app.services.metrics import build_comparison, compute_metrics, metrics_by_hour


def _comparison(actual: list[float], forecast: list[float | None]) -> pd.DataFrame:
    times = pd.date_range("2026-01-01T00:00Z", periods=len(actual), freq="h")
    actuals = pd.DataFrame({"start_time": times, "generation_mw": actual})
    selected = pd.DataFrame(
        {
            "start_time": times,
            "publish_time": times - pd.Timedelta(hours=5),
            "generation_mw": [float("nan") if f is None else f for f in forecast],
            "lead_hours": 5.0,
        }
    )
    return build_comparison(actuals, selected)


def test_error_sign_is_forecast_minus_actual() -> None:
    comp = _comparison([100.0], [130.0])
    assert comp.loc[0, "error_mw"] == 30.0


def test_basic_metrics() -> None:
    m = compute_metrics(_comparison([100, 100, 100, 100], [110, 90, 130, 100]))
    # errors: 10, -10, 30, 0
    assert m["mae"] == pytest.approx(12.5)
    assert m["rmse"] == pytest.approx(math.sqrt((100 + 100 + 900) / 4))
    assert m["bias"] == pytest.approx(7.5)
    assert m["mape"] == pytest.approx(12.5)
    assert m["nmae_pct"] == pytest.approx(12.5)
    assert m["coverage_pct"] == 100.0
    assert m["abs_error_percentiles"]["p50"] == pytest.approx(10.0)


def test_missing_forecasts_reduce_coverage_but_not_errors() -> None:
    m = compute_metrics(_comparison([100, 100, 100, 100], [110, None, None, 90]))
    assert m["n_slots"] == 4
    assert m["n_forecasts"] == 2
    assert m["coverage_pct"] == 50.0
    assert m["mae"] == pytest.approx(10.0)
    assert m["bias"] == pytest.approx(0.0)


def test_empty_window_returns_nulls() -> None:
    m = compute_metrics(_comparison([100.0], [None]))
    assert m["coverage_pct"] == 0.0
    assert m["mae"] is None
    assert m["error_percentiles"]["p90"] is None


def test_percentiles_ordering() -> None:
    comp = _comparison(list(range(1, 101)), [x + (x % 7) * 10 for x in range(1, 101)])
    p = compute_metrics(comp)["abs_error_percentiles"]
    assert p["p10"] <= p["p50"] <= p["p90"] <= p["p95"]


def test_metrics_by_hour_groups_by_utc_hour() -> None:
    rows = metrics_by_hour(_comparison([100, 100, 100], [110, 80, None]))
    assert len(rows) == 24
    assert rows[0] == {"hour": 0, "n": 1, "mae": 10.0, "rmse": 10.0, "bias": 10.0}
    assert rows[1]["bias"] == -20.0
    assert rows[2]["n"] == 0 and rows[2]["mae"] is None
