"""API tests against the committed January 2026 dataset."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["actual_rows"] == 31 * 48
    assert body["forecast_rows"] > 0


def test_actuals_window_is_inclusive() -> None:
    r = client.get(
        "/api/actuals", params={"start": "2026-01-05T00:00:00Z", "end": "2026-01-05T01:00:00Z"}
    )
    assert r.status_code == 200
    assert [p["start_time"] for p in r.json()] == [
        "2026-01-05T00:00:00Z",
        "2026-01-05T00:30:00Z",
        "2026-01-05T01:00:00Z",
    ]


def test_forecasts_respect_horizon() -> None:
    for horizon in (0, 4, 24):
        rows = client.get("/api/forecasts", params={"horizon": horizon}).json()
        leads = [r["lead_hours"] for r in rows if r["lead_hours"] is not None]
        assert leads and min(leads) >= horizon
        assert max(leads) <= 48


def test_comparison_error_consistency() -> None:
    rows = client.get(
        "/api/comparison",
        params={"start": "2026-01-15T00:00:00Z", "end": "2026-01-15T23:30:00Z", "horizon": 8},
    ).json()
    assert len(rows) == 24
    for r in rows:
        assert r["error_mw"] == pytest.approx(r["forecast_mw"] - r["actual_mw"])


def test_metrics_shape() -> None:
    body = client.get("/api/metrics", params={"horizon": 24}).json()
    assert body["horizon_hours"] == 24
    assert 0 <= body["coverage_pct"] <= 100
    assert body["rmse"] >= body["mae"] > 0
    assert set(body["abs_error_percentiles"]) == {"p10", "p50", "p90", "p95"}


def test_metrics_by_horizon_covers_0_to_48() -> None:
    rows = client.get("/api/metrics/by-horizon").json()
    assert [r["horizon_hours"] for r in rows] == list(range(49))
    assert rows[0]["coverage_pct"] == 100.0


def test_metrics_by_hour() -> None:
    rows = client.get("/api/metrics/by-hour", params={"horizon": 4}).json()
    assert [r["hour"] for r in rows] == list(range(24))
    assert sum(r["n"] for r in rows) == 744


@pytest.mark.parametrize("horizon", [-1, 49])
def test_invalid_horizon_rejected(horizon: int) -> None:
    assert client.get("/api/metrics", params={"horizon": horizon}).status_code == 422


def test_inverted_window_rejected() -> None:
    r = client.get(
        "/api/metrics", params={"start": "2026-01-20T00:00:00Z", "end": "2026-01-10T00:00:00Z"}
    )
    assert r.status_code == 422
