"""
Flood Guard — Prediction Schemas
===================================
Defines the shape of flood-risk predictions returned by the API.

One schema (FloodPredictionOut) is shared between the current-risk and
forecast-risk endpoints — both are rows from the same flood_predictions
table, distinguished only by which endpoint queried for them.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FloodPredictionOut(BaseModel):
    """
    Response shape for a single flood-risk prediction.
    Used for both the current-risk and forecast-risk endpoints.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    station_id: int
    timestamp: datetime
    flood_probability: float
    is_flood_risk: bool
    model_name: str
    model_threshold: float
    predicted_at: Optional[datetime]
