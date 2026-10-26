"""Download and clean January 2026 national wind data from Elexon BMRS.

Writes two CSV files to ``backend/data``:

* ``actuals.csv``   - FUELHH half-hourly wind outturn (start_time, generation_mw)
* ``forecasts.csv`` - WINDFOR forecasts (start_time, publish_time, generation_mw)

Usage::

    python backend/scripts/fetch_data.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

TARGET_START = pd.Timestamp("2026-01-01T00:00:00Z")
TARGET_END = pd.Timestamp("2026-01-31T23:30:00Z")
FORECAST_PUBLISH_FROM = datetime(2025, 12, 29, tzinfo=UTC)
MAX_LEAD = pd.Timedelta(hours=48)
CHUNK = timedelta(days=2)
TIMEOUT_S = 60


def _session() -> requests.Session:
    """Build a session that retries transient network and server errors."""
    retry = Retry(
        total=5,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


SESSION = _session()


def _get(url: str, params: dict[str, str]) -> list[dict]:
    """GET a BMRS stream endpoint and return the JSON list payload."""
    response = SESSION.get(url, params=params, timeout=TIMEOUT_S)
    response.raise_for_status()
    return response.json()


def fetch_actuals() -> pd.DataFrame:
    """Fetch FUELHH wind outturn for the target window.

    Settlement dates are in UK local time, so one extra day is requested on
    each side and the result is trimmed by UTC ``startTime``.
    """
    rows = _get(
        f"{BASE_URL}/FUELHH/stream",
        {
            "settlementDateFrom": "2025-12-31",
            "settlementDateTo": "2026-02-01",
            "fuelType": "WIND",
        },
    )
    df = pd.DataFrame(rows)
    df = df[df["fuelType"] == "WIND"]
    df = pd.DataFrame(
        {
            "start_time": pd.to_datetime(df["startTime"], utc=True),
            "publish_time": pd.to_datetime(df["publishTime"], utc=True),
            "generation_mw": pd.to_numeric(df["generation"], errors="coerce"),
        }
    ).dropna()
    df = df[(df["start_time"] >= TARGET_START) & (df["start_time"] <= TARGET_END)]
    # Keep the most recently published value if a slot was revised.
    df = df.sort_values(["start_time", "publish_time"]).drop_duplicates("start_time", keep="last")
    return df[["start_time", "generation_mw"]].reset_index(drop=True)


def fetch_forecasts() -> pd.DataFrame:
    """Fetch WINDFOR forecasts published from 29 Dec 2025 onwards.

    Only rows that can ever be selected are kept: target time inside the
    January window and a lead time (start - publish) between 0 and 48 hours.
    """
    frames: list[pd.DataFrame] = []
    publish_to_limit = TARGET_END.to_pydatetime()
    cursor = FORECAST_PUBLISH_FROM
    while cursor <= publish_to_limit:
        upper = min(cursor + CHUNK, publish_to_limit)
        rows = _get(
            f"{BASE_URL}/WINDFOR/stream",
            {
                "publishDateTimeFrom": cursor.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "publishDateTimeTo": upper.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )
        print(f"  WINDFOR {cursor:%Y-%m-%d %H:%M} -> {upper:%Y-%m-%d %H:%M}: {len(rows)} rows")
        if rows:
            frames.append(pd.DataFrame(rows))
        cursor = upper + timedelta(seconds=1)

    raw = pd.concat(frames, ignore_index=True)
    df = pd.DataFrame(
        {
            "start_time": pd.to_datetime(raw["startTime"], utc=True),
            "publish_time": pd.to_datetime(raw["publishTime"], utc=True),
            "generation_mw": pd.to_numeric(raw["generation"], errors="coerce"),
        }
    ).dropna()
    lead = df["start_time"] - df["publish_time"]
    df = df[
        (df["start_time"] >= TARGET_START)
        & (df["start_time"] <= TARGET_END)
        & (lead >= pd.Timedelta(0))
        & (lead <= MAX_LEAD)
    ]
    df = df.drop_duplicates(["start_time", "publish_time"], keep="last")
    return df.sort_values(["start_time", "publish_time"]).reset_index(drop=True)


def _save(df: pd.DataFrame, name: str) -> None:
    """Write a frame to ``DATA_DIR`` with ISO-8601 UTC timestamps."""
    out = df.copy()
    for col in out.columns:
        if col.endswith("_time"):
            out[col] = out[col].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    path = DATA_DIR / name
    out.to_csv(path, index=False)
    print(f"Wrote {len(out):,} rows to {path}")


def main() -> int:
    """Fetch, clean and persist both datasets."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("Fetching FUELHH actuals...")
    _save(fetch_actuals(), "actuals.csv")
    print("Fetching WINDFOR forecasts...")
    _save(fetch_forecasts(), "forecasts.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
