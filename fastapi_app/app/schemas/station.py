"""
Flood Guard — Station Schemas
==============================
Defines the shape of station data returned by the API.

Why a schema instead of returning the ORM model directly?
  The ORM model is a database object — it may contain internal fields,
  lazy-loaded relationships, or things you don't want to expose.
  The schema is the public contract: exactly what the caller receives.
"""

from pydantic import BaseModel, ConfigDict


class StationOut(BaseModel):
    """
    Response shape for a single station.
    Returned by GET /stations and embedded in weather responses.
    """

    model_config = ConfigDict(from_attributes=True)
    # from_attributes=True tells Pydantic: the data will come from a
    # SQLAlchemy ORM object (read from its .attributes), not a plain dict.

    id: int
    name: str
    latitude: float
    longitude: float
