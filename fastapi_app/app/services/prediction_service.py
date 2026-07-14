"""
Flood Guard — Prediction Service
===================================
All database queries related to flood-risk predictions live here.

Function responsibilities
--------------------------
  get_current_prediction    — the single "now" row for a station
  get_forecast_predictions  — upcoming risk predictions for a station, ordered by time

Services return ORM objects (or None / empty list).
They never raise HTTP exceptions — that is the router's responsibility.
"""

from sqlalchemy.orm import Session

from shared.database import FloodPrediction


def get_current_prediction(
    db: Session, station_id: int
) -> FloodPrediction | None:
    """
    Return the current flood-risk prediction for a station.
    Used by GET /predictions/{station_id} to show the "now" assessment.
    """
    return (
        db.query(FloodPrediction)
        .filter(
            FloodPrediction.station_id == station_id,
            FloodPrediction.is_current.is_(True),
        )
        .first()
    )


def get_forecast_predictions(
    db: Session, station_id: int
) -> list[FloodPrediction]:
    """
    Return all upcoming (non-current) flood-risk predictions for a station,
    ordered chronologically.
    Used by GET /predictions/{station_id}/forecast
    """
    return (
        db.query(FloodPrediction)
        .filter(
            FloodPrediction.station_id == station_id,
            FloodPrediction.is_current.is_(False),
        )
        .order_by(FloodPrediction.timestamp.asc())
        .all()
    )
