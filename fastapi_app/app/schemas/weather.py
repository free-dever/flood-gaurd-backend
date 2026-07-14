"""
Flood Guard — Weather Schemas
==============================
Defines the shape of weather data returned by the API.

One schema (WeatherRecordOut) is shared between historical and forecast
endpoints — both tables have identical columns, so the same shape fits both.

Fields are Optional (can be None) because Open-Meteo occasionally returns
null values for a variable in a given hour.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class WeatherRecordOut(BaseModel):
    """
    Response shape for a single hourly weather record.
    Used for both historical observations and forecast records.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    station_id: int
    timestamp: datetime
    precipitation_mm: Optional[float]
    temperature_c: Optional[float]
    wind_speed_kmh: Optional[float]
    relative_humidity_pct: Optional[float]
    fetched_at: Optional[datetime]
