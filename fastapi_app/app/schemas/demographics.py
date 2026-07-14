"""
Flood Guard — Demographics Schema
=================================
Defines the shape of demographics data returned by the API.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DemographicsOut(BaseModel):
    """Response shape for a station's population estimate."""

    model_config = ConfigDict(from_attributes=True)

    station_id:          int
    population_estimate: int
    radius_km:           float
    source:              str
    data_year:           int
    computed_at:         Optional[datetime]
