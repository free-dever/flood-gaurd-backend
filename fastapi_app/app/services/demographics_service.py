"""
Flood Guard — Demographics Service
====================================
DB queries related to station population estimates.
"""

from sqlalchemy.orm import Session

from shared.database import StationDemographics


def get_demographics_by_station(
    db: Session, station_id: int
) -> StationDemographics | None:
    """Return the demographics row for a station, or None if not yet computed."""
    return (
        db.query(StationDemographics)
        .filter_by(station_id=station_id)
        .first()
    )
