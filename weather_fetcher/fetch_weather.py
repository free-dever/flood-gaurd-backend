"""
Flood Guard — Weather Fetcher
==============================
Pulls hourly weather data from Open-Meteo and persists it to PostgreSQL.

What it does per station
-------------------------
  1. Seed    — ensure the station row exists in the stations table
  2. History — fetch past 30 days, insert new rows (duplicates silently skipped)
  3. Forecast — fetch next 7 days, replace all existing forecast rows for that
               station, then insert fresh ones

Variables fetched
-----------------
  precipitation_mm       — total rainfall per hour (mm)
  temperature_c          — air temperature at 2 m (°C)
  wind_speed_kmh         — wind speed at 10 m (km/h)
  relative_humidity_pct  — relative humidity at 2 m (%)
"""

import sys
import os
import time
from datetime import datetime, timezone

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database import SessionLocal, Station, WeatherHistorical, WeatherForecast
from weather_fetcher.config import (
    STATIONS,
    HISTORY_START, HISTORY_END,
    FORECAST_DAYS,
    OPENMETEO_ARCHIVE_URL,
    OPENMETEO_FORECAST_URL,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_BACKOFF_SECONDS,
)

HOURLY_VARS = [
    "precipitation",
    "temperature_2m",
    "wind_speed_10m",
    "relative_humidity_2m",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_with_retry(url: str, params: dict) -> requests.Response:
    """
    GET with a few retries on transient network errors (timeouts, connection
    resets). Open-Meteo occasionally times out on slower connections — e.g.
    GitHub Actions runners — and this job runs unattended twice a day with
    no one around to just retry it by hand.
    """
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                print(
                    f"(attempt {attempt}/{MAX_RETRIES} failed: {exc}; "
                    f"retrying in {RETRY_BACKOFF_SECONDS}s) ",
                    end="", flush=True,
                )
                time.sleep(RETRY_BACKOFF_SECONDS)
    raise last_exc


def _get_or_create_station(db, name: str, lat: float, lon: float) -> Station:
    """Return the Station row, creating it if it doesn't exist yet."""
    station = db.query(Station).filter_by(name=name).first()
    if not station:
        station = Station(name=name, latitude=lat, longitude=lon)
        db.add(station)
        db.commit()
        db.refresh(station)
        print(f"      Station '{name}' created (id={station.id})")
    return station


def _parse_hourly(data: dict) -> list[dict]:
    """Unpack an Open-Meteo hourly JSON block into a list of row dicts."""
    hourly = data["hourly"]
    rows = []
    for i, ts_str in enumerate(hourly["time"]):
        rows.append({
            "timestamp":             datetime.fromisoformat(ts_str).replace(
                                         tzinfo=timezone.utc
                                     ),
            "precipitation_mm":      hourly["precipitation"][i],
            "temperature_c":         hourly["temperature_2m"][i],
            "wind_speed_kmh":        hourly["wind_speed_10m"][i],
            "relative_humidity_pct": hourly["relative_humidity_2m"][i],
        })
    return rows


# ── Fetch functions ───────────────────────────────────────────────────────────

def fetch_and_store_historical(db, station: Station) -> int:
    """
    Fetch historical hourly weather for the 30-day window and insert into
    weather_historical. Rows that already exist are skipped via the unique
    constraint (station_id, timestamp).
    Returns the number of newly inserted rows.
    """
    params = {
        "latitude":   station.latitude,
        "longitude":  station.longitude,
        "start_date": HISTORY_START.isoformat(),
        "end_date":   HISTORY_END.isoformat(),
        "hourly":     ",".join(HOURLY_VARS),
        "timezone":   "Africa/Kampala",
    }
    resp = _get_with_retry(OPENMETEO_ARCHIVE_URL, params)

    rows = _parse_hourly(resp.json())
    inserted = 0
    for row in rows:
        exists = (
            db.query(WeatherHistorical)
            .filter_by(station_id=station.id, timestamp=row["timestamp"])
            .first()
        )
        if not exists:
            db.add(WeatherHistorical(station_id=station.id, **row))
            inserted += 1

    db.commit()
    return inserted


def fetch_and_store_forecast(db, station: Station) -> int:
    """
    Fetch the next FORECAST_DAYS days of hourly forecast data.
    Deletes all existing forecast rows for this station first, then inserts
    the fresh batch. Returns the number of inserted rows.
    """
    params = {
        "latitude":      station.latitude,
        "longitude":     station.longitude,
        "hourly":        ",".join(HOURLY_VARS),
        "forecast_days": FORECAST_DAYS,
        "timezone":      "Africa/Kampala",
    }
    resp = _get_with_retry(OPENMETEO_FORECAST_URL, params)

    # Wipe stale forecast rows for this station
    db.query(WeatherForecast).filter_by(station_id=station.id).delete()

    rows = _parse_hourly(resp.json())
    for row in rows:
        db.add(WeatherForecast(station_id=station.id, **row))

    db.commit()
    return len(rows)


# ── Runner ────────────────────────────────────────────────────────────────────

def run() -> None:
    db = SessionLocal()
    try:
        for name, lat, lon in STATIONS:
            print(f"\n  [{name}]")

            station = _get_or_create_station(db, name, lat, lon)

            print(f"    historical  ...", end=" ", flush=True)
            inserted = fetch_and_store_historical(db, station)
            print(f"{inserted} new rows stored")

            print(f"    forecast    ...", end=" ", flush=True)
            inserted = fetch_and_store_forecast(db, station)
            print(f"{inserted} rows stored (replaced)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
