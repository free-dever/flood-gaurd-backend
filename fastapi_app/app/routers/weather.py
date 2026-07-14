"""
Flood Guard — Weather Router
==============================
Handles all HTTP endpoints related to weather data.

Endpoints
---------
  GET /weather/{station_id}              — latest weather observation
  GET /weather/{station_id}/history      — historical records by date range
  GET /weather/{station_id}/forecast     — upcoming forecast records
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from fastapi_app.app.db.deps import get_db
from fastapi_app.app.schemas.weather import WeatherRecordOut
from fastapi_app.app.services import station_service, weather_service

router = APIRouter(prefix="/weather", tags=["Weather"])


# ── Station guard helper ──────────────────────────────────────────────────────
# All three endpoints below need to confirm the station exists first.
# Extracting that check into a helper keeps each route clean and avoids
# repeating the same four lines three times.

def _require_station(station_id: int, db: Session):
    """Raise 404 if the station doesn't exist, otherwise return it."""
    station = station_service.get_station_by_id(db, station_id)
    if station is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with id={station_id} not found.",
        )
    return station


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/{station_id}", response_model=WeatherRecordOut)
def get_current_weather(station_id: int, db: Session = Depends(get_db)):
    """
    Return the most recent historical weather observation for a station.

    This is the 'current conditions' endpoint — it picks the latest
    row from weather_historical ordered by timestamp descending.
    """
    _require_station(station_id, db)

    record = weather_service.get_latest_weather(db, station_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No weather data found for station id={station_id}.",
        )
    return record


@router.get("/{station_id}/history", response_model=list[WeatherRecordOut])
def get_weather_history(
    station_id: int,
    start_date: date = Query(..., description="Start date inclusive (YYYY-MM-DD)"),
    end_date:   date = Query(..., description="End date inclusive (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Return hourly historical weather records for a station within a date range.

    Query parameters:
      - start_date: first day to include (YYYY-MM-DD)
      - end_date:   last day to include  (YYYY-MM-DD)

    Example:
      GET /weather/2/history?start_date=2026-06-01&end_date=2026-06-15
    """
    _require_station(station_id, db)

    # Sanity-check the date range — the service won't catch this.
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="start_date must be on or before end_date.",
        )

    return weather_service.get_historical_weather(db, station_id, start_date, end_date)


@router.get("/{station_id}/forecast", response_model=list[WeatherRecordOut])
def get_weather_forecast(station_id: int, db: Session = Depends(get_db)):
    """
    Return all upcoming forecast records for a station, ordered by time.

    Forecast data is refreshed every time the weather fetcher runs.
    """
    _require_station(station_id, db)

    return weather_service.get_forecast_weather(db, station_id)
