"""
Flood Guard — Weather Service
==============================
All database queries related to weather records live here.

Function responsibilities
-------------------------
  get_latest_weather       — most recent historical record for a station
  get_historical_weather   — historical records filtered by a date range
  get_forecast_weather     — all forecast records for a station, ordered by time

Services return ORM objects (or None / empty list).
They never raise HTTP exceptions — that is the router's responsibility.
"""

from datetime import date

from sqlalchemy.orm import Session

from shared.database import WeatherHistorical, WeatherForecast


def get_latest_weather(
    db: Session, station_id: int
) -> WeatherHistorical | None:
    """
    Return the single most recent historical weather record for a station.
    Used by GET /weather/{station_id} to show current conditions.
    """
    return (
        db.query(WeatherHistorical)
        .filter(WeatherHistorical.station_id == station_id)
        .order_by(WeatherHistorical.timestamp.desc())
        .first()
    )


def get_historical_weather(
    db: Session,
    station_id: int,
    start_date: date,
    end_date: date,
) -> list[WeatherHistorical]:
    """
    Return historical records for a station within a date range (inclusive).
    Used by GET /weather/{station_id}/history?start_date=&end_date=

    The date comparison casts the timestamptz column to a date so callers
    can pass simple YYYY-MM-DD values without worrying about time zones.
    """
    return (
        db.query(WeatherHistorical)
        .filter(
            WeatherHistorical.station_id == station_id,
            WeatherHistorical.timestamp >= start_date.isoformat(),
            WeatherHistorical.timestamp <  end_date.isoformat() + "T23:59:59",
        )
        .order_by(WeatherHistorical.timestamp.asc())
        .all()
    )


def get_forecast_weather(
    db: Session, station_id: int
) -> list[WeatherForecast]:
    """
    Return all forecast records for a station, ordered chronologically.
    Used by GET /weather/{station_id}/forecast
    """
    return (
        db.query(WeatherForecast)
        .filter(WeatherForecast.station_id == station_id)
        .order_by(WeatherForecast.timestamp.asc())
        .all()
    )
