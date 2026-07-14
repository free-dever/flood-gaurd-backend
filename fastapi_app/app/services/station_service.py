"""
Flood Guard — Station Service
==============================
All database queries related to stations live here.

Services return ORM objects (or None). They never raise HTTP exceptions
— that is the router's responsibility.
"""

from sqlalchemy.orm import Session

from shared.database import Station


def get_all_stations(db: Session) -> list[Station]:
    """Return every station row, ordered by name."""
    return db.query(Station).order_by(Station.name).all()


def get_station_by_id(db: Session, station_id: int) -> Station | None:
    """Return a single station by primary key, or None if not found."""
    return db.query(Station).filter(Station.id == station_id).first()
