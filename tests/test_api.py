"""
Flood Guard — Integration Tests
=================================
Tests the full stack: FastAPI routes → services → Neon PostgreSQL.

Uses FastAPI's TestClient, which sends requests directly through the app
without needing a running uvicorn server. The real Neon database is used,
so these tests verify the genuine end-to-end flow.

Run from the project root:
    pytest tests/ -v
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from fastapi_app.app.main import app

# One shared client for all tests — TestClient wraps the app directly.
client = TestClient(app)

# Station we'll use throughout — kampala_city_centre (id=2).
# This is known to have data from the weather fetcher run.
STATION_ID   = 2
STATION_NAME = "kampala_city_centre"

# Date range guaranteed to fall inside the stored 30-day historical window.
# Using dynamic dates keeps tests valid on any future run day.
_end   = date.today() - timedelta(days=3)
_start = _end - timedelta(days=1)
HISTORY_START = _start.isoformat()   # 2-day window → expect 48 rows
HISTORY_END   = _end.isoformat()


# ── Health ────────────────────────────────────────────────────────────────────

def test_health():
    """Server is reachable and returns the expected status payload."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── Stations ──────────────────────────────────────────────────────────────────

def test_list_stations_returns_all_four():
    """GET /stations returns all 4 Kampala monitoring stations."""
    response = client.get("/stations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    # Results are ordered by name — check the expected names are all present.
    names = {s["name"] for s in data}
    assert names == {
        "kampala_city_centre",
        "nakivubo_channel",
        "lubigi_wetland",
        "bwaise",
    }


def test_list_stations_response_shape():
    """Each station object has exactly the expected fields."""
    response = client.get("/stations")
    station = response.json()[0]
    assert set(station.keys()) == {"id", "name", "latitude", "longitude"}


def test_get_station_by_id():
    """GET /stations/{id} returns the correct station."""
    response = client.get(f"/stations/{STATION_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"]   == STATION_ID
    assert data["name"] == STATION_NAME


def test_get_station_not_found():
    """GET /stations/999 returns 404 for a non-existent station."""
    response = client.get("/stations/999")
    assert response.status_code == 404


# ── Current weather ───────────────────────────────────────────────────────────

def test_get_current_weather():
    """GET /weather/{id} returns a single record with all expected fields."""
    response = client.get(f"/weather/{STATION_ID}")
    assert response.status_code == 200
    data = response.json()
    # Check the record belongs to the right station
    assert data["station_id"] == STATION_ID
    # Check all weather fields are present (values may be None but keys exist)
    for field in ("precipitation_mm", "temperature_c", "wind_speed_kmh",
                  "relative_humidity_pct"):
        assert field in data


def test_get_current_weather_station_not_found():
    """GET /weather/999 returns 404 for a non-existent station."""
    response = client.get("/weather/999")
    assert response.status_code == 404


# ── Historical weather ────────────────────────────────────────────────────────

def test_get_history_valid_range():
    """
    GET /weather/{id}/history returns 48 rows for a 2-day window
    (2 days × 24 hourly records).
    """
    response = client.get(
        f"/weather/{STATION_ID}/history",
        params={"start_date": HISTORY_START, "end_date": HISTORY_END},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 48


def test_get_history_ordered_ascending():
    """History records are returned oldest-first."""
    response = client.get(
        f"/weather/{STATION_ID}/history",
        params={"start_date": HISTORY_START, "end_date": HISTORY_END},
    )
    timestamps = [r["timestamp"] for r in response.json()]
    assert timestamps == sorted(timestamps)


def test_get_history_bad_date_range():
    """start_date after end_date returns 422 Unprocessable Entity."""
    response = client.get(
        f"/weather/{STATION_ID}/history",
        params={"start_date": HISTORY_END, "end_date": HISTORY_START},
    )
    assert response.status_code == 422


def test_get_history_missing_params():
    """Omitting required query params returns 422."""
    response = client.get(f"/weather/{STATION_ID}/history")
    assert response.status_code == 422


def test_get_history_station_not_found():
    """History for a non-existent station returns 404."""
    response = client.get(
        "/weather/999/history",
        params={"start_date": HISTORY_START, "end_date": HISTORY_END},
    )
    assert response.status_code == 404


# ── Forecast weather ──────────────────────────────────────────────────────────

def test_get_forecast_returns_rows():
    """GET /weather/{id}/forecast returns 168 rows (7 days × 24 hours)."""
    response = client.get(f"/weather/{STATION_ID}/forecast")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 7 * 24


def test_get_forecast_ordered_ascending():
    """Forecast records are returned chronologically."""
    response = client.get(f"/weather/{STATION_ID}/forecast")
    timestamps = [r["timestamp"] for r in response.json()]
    assert timestamps == sorted(timestamps)


def test_get_forecast_station_not_found():
    """Forecast for a non-existent station returns 404."""
    response = client.get("/weather/999/forecast")
    assert response.status_code == 404


# ── Flood predictions ─────────────────────────────────────────────────────────

def test_get_current_prediction():
    """GET /predictions/{id} returns a single prediction with all expected fields."""
    response = client.get(f"/predictions/{STATION_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data["station_id"] == STATION_ID
    for field in ("flood_probability", "is_flood_risk", "model_name", "model_threshold"):
        assert field in data


def test_get_current_prediction_station_not_found():
    """GET /predictions/999 returns 404 for a non-existent station."""
    response = client.get("/predictions/999")
    assert response.status_code == 404


def test_get_forecast_predictions_returns_rows():
    """
    GET /predictions/{id}/forecast returns a non-empty list of upcoming
    predictions. Not an exact 7*24 count (unlike the weather forecast test)
    since hours with incomplete rolling-window data are silently dropped.
    """
    response = client.get(f"/predictions/{STATION_ID}/forecast")
    assert response.status_code == 200
    data = response.json()
    assert 0 < len(data) <= 7 * 24


def test_get_forecast_predictions_ordered_ascending():
    """Forecast predictions are returned chronologically."""
    response = client.get(f"/predictions/{STATION_ID}/forecast")
    timestamps = [r["timestamp"] for r in response.json()]
    assert timestamps == sorted(timestamps)


def test_get_forecast_predictions_station_not_found():
    """Forecast predictions for a non-existent station return 404."""
    response = client.get("/predictions/999/forecast")
    assert response.status_code == 404
