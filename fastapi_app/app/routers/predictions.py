"""
Flood Guard — Predictions Router
===================================
Handles all HTTP endpoints related to flood-risk predictions.

Endpoints
---------
  GET /predictions/{station_id}           — current flood-risk prediction
  GET /predictions/{station_id}/forecast  — upcoming flood-risk predictions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from fastapi_app.app.db.deps import get_db
from fastapi_app.app.schemas.prediction import FloodPredictionOut
from fastapi_app.app.services import station_service, prediction_service

router = APIRouter(prefix="/predictions", tags=["Predictions"])


# ── Station guard helper ──────────────────────────────────────────────────────
# Both endpoints below need to confirm the station exists first.

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

@router.get("/{station_id}", response_model=FloodPredictionOut)
def get_current_prediction(station_id: int, db: Session = Depends(get_db)):
    """
    Return the current flood-risk prediction for a station — the model's
    output for the latest known weather observation ("now").
    """
    _require_station(station_id, db)

    record = prediction_service.get_current_prediction(db, station_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No flood-risk prediction available for station id={station_id}. "
                   "Run model_service/run.py to compute it.",
        )
    return record


@router.get("/{station_id}/forecast", response_model=list[FloodPredictionOut])
def get_forecast_predictions(station_id: int, db: Session = Depends(get_db)):
    """
    Return all upcoming flood-risk predictions for a station, ordered by time.

    Predictions are refreshed every time the prediction job (model_service/run.py) runs.
    """
    _require_station(station_id, db)

    return prediction_service.get_forecast_predictions(db, station_id)
