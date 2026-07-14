"""
Flood Guard — Stations Router
==============================
Handles all HTTP endpoints related to monitoring stations.

Endpoints
---------
  GET /stations            — list all stations
  GET /stations/{id}       — get a single station by ID
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from fastapi_app.app.db.deps import get_db
from fastapi_app.app.schemas.station import StationOut
from fastapi_app.app.services import station_service

# APIRouter groups these routes together.
# prefix="/stations" means every route below is automatically under /stations.
# tags=["Stations"] groups them under one heading in Swagger UI.
router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get("", response_model=list[StationOut])
def list_stations(db: Session = Depends(get_db)):
    """
    Return all monitoring stations.

    - db is injected automatically by FastAPI via Depends(get_db)
    - The service does the DB query and returns ORM objects
    - FastAPI uses StationOut to serialise each object into JSON
    """
    return station_service.get_all_stations(db)


@router.get("/{station_id}", response_model=StationOut)
def get_station(station_id: int, db: Session = Depends(get_db)):
    """
    Return a single station by its ID.

    FastAPI automatically parses {station_id} from the URL as an int.
    If the service returns None (station not found), we raise a 404 —
    this is the router's responsibility, not the service's.
    """
    station = station_service.get_station_by_id(db, station_id)
    if station is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with id={station_id} not found.",
        )
    return station
