"""
Flood Guard — Demographics Router
===================================
Endpoints
---------
  GET /stations/{station_id}/demographics — population estimate for a station
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from fastapi_app.app.db.deps import get_db
from fastapi_app.app.schemas.demographics import DemographicsOut
from fastapi_app.app.services import station_service, demographics_service

# Note the prefix — this router hangs off /stations so the URL reads
# naturally as GET /stations/{station_id}/demographics
router = APIRouter(prefix="/stations", tags=["Demographics"])


@router.get("/{station_id}/demographics", response_model=DemographicsOut)
def get_station_demographics(station_id: int, db: Session = Depends(get_db)):
    """
    Return the population estimate for the flood zone surrounding a station.

    The estimate covers all people within a 1 km radius of the station
    coordinates, sourced from WorldPop 2020 census-adjusted data.
    """
    # Confirm the station exists first
    if station_service.get_station_by_id(db, station_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with id={station_id} not found.",
        )

    record = demographics_service.get_demographics_by_station(db, station_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No demographics data available for station id={station_id}. "
                   "Run demographics_fetcher/run.py to compute it.",
        )
    return record
