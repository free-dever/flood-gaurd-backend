"""
Flood Guard — Shared Database Layer
=====================================
Defines the SQLAlchemy engine, session factory, and all ORM table models.

Tables
------
  stations              — monitoring locations (single source of truth)
  weather_historical    — append-only historical observations
  weather_forecast      — daily-refreshed forecast records (replaced each run)
  station_demographics  — population estimates per station zone (static, updated rarely)
  flood_predictions     — model-predicted flood risk, current + forecast (replaced each run)
"""

import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, UniqueConstraint, create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from shared.settings import DATABASE_URL

# ── Engine ────────────────────────────────────────────────────────────────────
# pool_pre_ping=True keeps connections healthy after Neon scales to zero.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# ── ORM base ──────────────────────────────────────────────────────────────────
Base = declarative_base()


# ── Models ────────────────────────────────────────────────────────────────────

class Station(Base):
    """A physical monitoring location."""

    __tablename__ = "stations"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    name      = Column(String(100), nullable=False, unique=True)
    latitude  = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    historical_records  = relationship("WeatherHistorical",    back_populates="station")
    forecast_records    = relationship("WeatherForecast",      back_populates="station")
    demographics        = relationship("StationDemographics", back_populates="station", uselist=False)
    prediction_records  = relationship("FloodPrediction",     back_populates="station")

    def __repr__(self) -> str:
        return f"<Station id={self.id} name={self.name!r}>"


class WeatherHistorical(Base):
    """
    Hourly historical weather observations.
    Rows are append-only — never deleted or overwritten.
    A unique constraint on (station_id, timestamp) prevents duplicates
    when the fetcher re-runs for overlapping date windows.
    """

    __tablename__ = "weather_historical"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    station_id            = Column(Integer, ForeignKey("stations.id"), nullable=False)
    timestamp             = Column(DateTime(timezone=True), nullable=False)
    precipitation_mm      = Column(Float, nullable=True)
    temperature_c         = Column(Float, nullable=True)
    wind_speed_kmh        = Column(Float, nullable=True)
    relative_humidity_pct = Column(Float, nullable=True)
    fetched_at            = Column(
        DateTime(timezone=True), default=datetime.datetime.utcnow
    )

    station = relationship("Station", back_populates="historical_records")

    __table_args__ = (
        UniqueConstraint(
            "station_id", "timestamp",
            name="uq_historical_station_timestamp",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<WeatherHistorical station_id={self.station_id} "
            f"timestamp={self.timestamp}>"
        )


class WeatherForecast(Base):
    """
    Hourly weather forecast records.
    This table is fully replaced on every fetcher run:
    all rows for a station are deleted, then fresh forecast rows inserted.
    A unique constraint on (station_id, timestamp) guards against
    partial double-inserts.
    """

    __tablename__ = "weather_forecast"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    station_id            = Column(Integer, ForeignKey("stations.id"), nullable=False)
    timestamp             = Column(DateTime(timezone=True), nullable=False)
    precipitation_mm      = Column(Float, nullable=True)
    temperature_c         = Column(Float, nullable=True)
    wind_speed_kmh        = Column(Float, nullable=True)
    relative_humidity_pct = Column(Float, nullable=True)
    fetched_at            = Column(
        DateTime(timezone=True), default=datetime.datetime.utcnow
    )

    station = relationship("Station", back_populates="forecast_records")

    __table_args__ = (
        UniqueConstraint(
            "station_id", "timestamp",
            name="uq_forecast_station_timestamp",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<WeatherForecast station_id={self.station_id} "
            f"timestamp={self.timestamp}>"
        )


class StationDemographics(Base):
    """
    Population estimate for the zone around a monitoring station.

    One row per station. Updated by running the demographics fetcher
    (demographics_fetcher/run.py) — not on every weather fetch cycle
    since population data changes infrequently.

    radius_km   — the circular buffer radius used to sum population pixels
    data_year   — the WorldPop dataset year the estimate comes from
    source      — data provider label (e.g. 'worldpop')
    computed_at — when this estimate was last computed
    """

    __tablename__ = "station_demographics"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    station_id          = Column(Integer, ForeignKey("stations.id"), nullable=False, unique=True)
    population_estimate = Column(Integer, nullable=False)
    radius_km           = Column(Float, nullable=False)
    source              = Column(String(50), nullable=False, default="worldpop")
    data_year           = Column(Integer, nullable=False)
    computed_at         = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    station = relationship("Station", back_populates="demographics")

    def __repr__(self) -> str:
        return (
            f"<StationDemographics station_id={self.station_id} "
            f"population={self.population_estimate} radius={self.radius_km}km>"
        )


class FloodPrediction(Base):
    """
    Model-predicted flood risk, one row per station per hour, spanning from
    the current hour ("now") through the end of the forecast horizon.

    Like weather_forecast, this table is fully replaced on every prediction
    job run: all rows for a station are deleted, then freshly predicted rows
    inserted (see model_service/predict_flood_risk.py).

    is_current flags the single row for "now" — what GET /predictions/{id}
    returns. All other rows (is_current=False) are forecast-horizon
    predictions, returned by GET /predictions/{id}/forecast.

    model_name / model_threshold record which model + decision threshold
    produced each row — an audit trail so predictions stay self-describing
    if the served model is ever swapped.
    """

    __tablename__ = "flood_predictions"

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    station_id         = Column(Integer, ForeignKey("stations.id"), nullable=False)
    timestamp          = Column(DateTime(timezone=True), nullable=False)
    flood_probability  = Column(Float, nullable=False)
    is_flood_risk      = Column(Boolean, nullable=False)
    is_current         = Column(Boolean, nullable=False, default=False)
    model_name         = Column(String(50), nullable=False)
    model_threshold    = Column(Float, nullable=False)
    predicted_at       = Column(
        DateTime(timezone=True), default=datetime.datetime.utcnow
    )

    station = relationship("Station", back_populates="prediction_records")

    __table_args__ = (
        UniqueConstraint(
            "station_id", "timestamp",
            name="uq_prediction_station_timestamp",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<FloodPrediction station_id={self.station_id} "
            f"timestamp={self.timestamp} probability={self.flood_probability:.3f} "
            f"risk={self.is_flood_risk}>"
        )


# ── Table creation ─────────────────────────────────────────────────────────────

def create_all_tables() -> None:
    """Create all tables in the database if they do not already exist."""
    Base.metadata.create_all(bind=engine)
    print(
        "Tables created: stations, weather_historical, weather_forecast, "
        "station_demographics, flood_predictions"
    )


if __name__ == "__main__":
    create_all_tables()
