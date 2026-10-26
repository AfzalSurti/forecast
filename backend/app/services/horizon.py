"""Forecast horizon selection.

For a horizon ``H`` and a target time ``T`` the usable forecast is the one
with the latest ``publish_time`` such that ``publish_time <= T - H``. Forecasts
published more than ``max_lead_hours`` before ``T`` are discarded, and no
later forecast is ever used as a fallback: if nothing qualifies the value is
missing.
"""

from __future__ import annotations

import pandas as pd

MAX_LEAD_HOURS = 48


def select_forecasts(
    forecasts: pd.DataFrame,
    horizon_hours: float,
    targets: pd.Series | None = None,
    max_lead_hours: float = MAX_LEAD_HOURS,
) -> pd.DataFrame:
    """Pick one forecast per target time for the given horizon.

    Args:
        forecasts: Frame with ``start_time``, ``publish_time`` and
            ``generation_mw`` columns (tz-aware UTC timestamps).
        horizon_hours: Minimum gap between publication and target time.
        targets: Target start times to evaluate. Defaults to every distinct
            ``start_time`` in ``forecasts``.
        max_lead_hours: Forecasts older than this relative to the target are
            discarded.

    Returns:
        One row per target with ``start_time``, ``publish_time``,
        ``generation_mw`` and ``lead_hours``; the last three are missing (NaT /
        NaN) where no forecast qualifies.
    """
    if not 0 <= horizon_hours <= max_lead_hours:
        raise ValueError(f"horizon_hours must be within [0, {max_lead_hours}]")

    if targets is None:
        targets = forecasts["start_time"]
    left = pd.DataFrame({"start_time": pd.Series(targets).drop_duplicates().reset_index(drop=True)})
    left["cutoff"] = left["start_time"] - pd.Timedelta(hours=horizon_hours)
    left = left.sort_values("cutoff")

    right = forecasts[["start_time", "publish_time", "generation_mw"]].sort_values("publish_time")

    merged = pd.merge_asof(
        left,
        right,
        left_on="cutoff",
        right_on="publish_time",
        by="start_time",
        direction="backward",
        allow_exact_matches=True,
    )

    lead = merged["start_time"] - merged["publish_time"]
    too_old = lead > pd.Timedelta(hours=max_lead_hours)
    merged.loc[too_old, "publish_time"] = pd.NaT
    merged.loc[too_old, "generation_mw"] = float("nan")
    merged["lead_hours"] = (
        merged["start_time"] - merged["publish_time"]
    ).dt.total_seconds() / 3600.0

    return merged.drop(columns="cutoff").sort_values("start_time").reset_index(drop=True)
