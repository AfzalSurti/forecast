"""Tests for horizon-based forecast selection."""

import math

import pandas as pd
import pytest

from app.services.horizon import select_forecasts

T = pd.Timestamp("2026-01-10T12:00:00Z")


def _forecasts(rows: list[tuple[str, str, float]]) -> pd.DataFrame:
    """Build a forecasts frame from ``(start_time, publish_time, mw)`` tuples."""
    df = pd.DataFrame(rows, columns=["start_time", "publish_time", "generation_mw"])
    df["start_time"] = pd.to_datetime(df["start_time"], utc=True)
    df["publish_time"] = pd.to_datetime(df["publish_time"], utc=True)
    return df


def _one(df: pd.DataFrame, horizon: float) -> pd.Series:
    out = select_forecasts(df, horizon)
    assert len(out) == 1
    return out.iloc[0]


def test_picks_latest_publish_at_or_before_cutoff() -> None:
    df = _forecasts(
        [
            ("2026-01-10T12:00Z", "2026-01-10T02:00Z", 100.0),
            ("2026-01-10T12:00Z", "2026-01-10T06:00Z", 200.0),
            ("2026-01-10T12:00Z", "2026-01-10T09:00Z", 300.0),
        ]
    )
    row = _one(df, 4)  # cutoff 08:00 -> 06:00 forecast
    assert row["generation_mw"] == 200.0
    assert row["publish_time"] == pd.Timestamp("2026-01-10T06:00Z")
    assert row["lead_hours"] == 6.0


def test_exact_boundary_is_included() -> None:
    df = _forecasts(
        [
            ("2026-01-10T12:00Z", "2026-01-10T06:00Z", 200.0),
            ("2026-01-10T12:00Z", "2026-01-10T08:00Z", 250.0),
        ]
    )
    row = _one(df, 4)  # publish 08:00 == T - 4h exactly
    assert row["generation_mw"] == 250.0
    assert row["lead_hours"] == 4.0


def test_never_falls_back_to_later_forecast() -> None:
    df = _forecasts([("2026-01-10T12:00Z", "2026-01-10T09:00Z", 300.0)])
    row = _one(df, 4)  # only forecast is 3h ahead, too late for H=4
    assert math.isnan(row["generation_mw"])
    assert pd.isna(row["publish_time"])


def test_forecast_older_than_48h_is_discarded() -> None:
    df = _forecasts([("2026-01-10T12:00Z", "2026-01-08T11:00Z", 100.0)])  # 49h lead
    row = _one(df, 24)
    assert math.isnan(row["generation_mw"])
    assert pd.isna(row["lead_hours"])


def test_forecast_exactly_48h_is_kept() -> None:
    df = _forecasts([("2026-01-10T12:00Z", "2026-01-08T12:00Z", 100.0)])
    row = _one(df, 48)
    assert row["generation_mw"] == 100.0
    assert row["lead_hours"] == 48.0


def test_horizon_zero_uses_latest_published_before_target() -> None:
    df = _forecasts(
        [
            ("2026-01-10T12:00Z", "2026-01-10T11:30Z", 500.0),
            ("2026-01-10T12:00Z", "2026-01-10T12:30Z", 999.0),  # after target
        ]
    )
    assert _one(df, 0)["generation_mw"] == 500.0


def test_forecasts_do_not_leak_across_target_times() -> None:
    df = _forecasts(
        [
            ("2026-01-10T12:00Z", "2026-01-10T01:00Z", 100.0),
            ("2026-01-10T13:00Z", "2026-01-10T07:00Z", 900.0),
        ]
    )
    out = select_forecasts(df, 4).set_index("start_time")
    assert out.loc[pd.Timestamp("2026-01-10T12:00Z"), "generation_mw"] == 100.0
    assert out.loc[pd.Timestamp("2026-01-10T13:00Z"), "generation_mw"] == 900.0


def test_explicit_targets_without_forecasts_are_missing() -> None:
    df = _forecasts([("2026-01-10T12:00Z", "2026-01-10T01:00Z", 100.0)])
    targets = pd.Series(pd.to_datetime(["2026-01-10T12:00Z", "2026-01-10T12:30Z"], utc=True))
    out = select_forecasts(df, 1, targets=targets)
    assert list(out["generation_mw"].isna()) == [False, True]


@pytest.mark.parametrize("horizon", [-1, 48.5])
def test_rejects_out_of_range_horizon(horizon: float) -> None:
    df = _forecasts([("2026-01-10T12:00Z", "2026-01-10T01:00Z", 100.0)])
    with pytest.raises(ValueError):
        select_forecasts(df, horizon)
