"""Tests for environment-driven settings."""

import pytest

from app.config import Settings


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://a.vercel.app", ["https://a.vercel.app"]),
        (
            "https://a.vercel.app/, http://localhost:5173",
            ["https://a.vercel.app", "http://localhost:5173"],
        ),
        ('["https://a.vercel.app/"]', ["https://a.vercel.app"]),
        ("*", ["*"]),
    ],
)
def test_cors_origins_from_env(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: list[str]
) -> None:
    monkeypatch.setenv("FORECAST_CORS_ORIGINS", raw)
    assert Settings().cors_origins == expected


def test_cors_origins_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FORECAST_CORS_ORIGINS", raising=False)
    assert Settings().cors_origins == ["*"]
