"""
Flood Guard — Demographics Fetcher
=====================================
Fetches population estimates from the WorldPop REST API for each monitoring
station and persists them to the station_demographics table.

How it works
------------
For each station:
  1. Build a circular polygon (32 vertices) centred on the station's lat/lon
     using the configured RADIUS_KM.
  2. POST that GeoJSON polygon to the WorldPop stats endpoint.
  3. Parse the total population from the response.
  4. Upsert into station_demographics — update if the row already exists
     (so re-running the fetcher refreshes estimates without creating duplicates).

No API key required — WorldPop is free and open.
"""

import json
import math
import os
import sys
from datetime import datetime, timezone

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database import SessionLocal, Station, StationDemographics
from demographics_fetcher.config import (
    STATIONS,
    RADIUS_KM,
    WORLDPOP_STATS_URL,
    WORLDPOP_DATASET,
    DATA_YEAR,
    SOURCE_LABEL,
    REQUEST_TIMEOUT,
    CIRCLE_POINTS,
)


# ── Geometry helpers ──────────────────────────────────────────────────────────

def _circle_polygon(lat: float, lon: float, radius_km: float, n: int) -> dict:
    """
    Return a GeoJSON FeatureCollection containing one Polygon that approximates
    a circle of radius_km around (lat, lon).

    Maths:
      1 degree of latitude  ≈ 111 km everywhere.
      1 degree of longitude ≈ 111 km × cos(latitude).
    At Kampala (~0.3 °N) cos(0.3°) ≈ 1.0, so both are effectively equal.
    """
    lat_rad = math.radians(lat)
    d_lat = radius_km / 111.0
    d_lon = radius_km / (111.0 * math.cos(lat_rad))

    coords = []
    for i in range(n):
        angle = 2 * math.pi * i / n
        coords.append([
            lon + d_lon * math.sin(angle),
            lat + d_lat * math.cos(angle),
        ])
    coords.append(coords[0])   # close the ring

    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords],
            },
        }],
    }


# ── WorldPop API ──────────────────────────────────────────────────────────────

def _fetch_population(lat: float, lon: float) -> int:
    """
    Query the WorldPop stats API for total population within a 1-km circle
    around (lat, lon). Returns the rounded integer population estimate.
    """
    geojson = _circle_polygon(lat, lon, RADIUS_KM, CIRCLE_POINTS)

    params = {
        "dataset":  WORLDPOP_DATASET,
        "year":     DATA_YEAR,
        "geojson":  json.dumps(geojson),
        "runasync": "false",
    }

    resp = requests.get(WORLDPOP_STATS_URL, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    payload = resp.json()

    # WorldPop returns: {"status": "started", "error": false, "data": {"total_population": 12345.6}}
    if payload.get("error") or payload.get("status_code") != 200:
        raise RuntimeError(f"WorldPop API error: {payload}")

    population = payload["data"]["total_population"]
    return round(population)


# ── DB upsert ─────────────────────────────────────────────────────────────────

def _upsert_demographics(
    db, station: Station, population: int
) -> None:
    """
    Insert a new demographics row for this station, or update it if one
    already exists (so re-runs refresh estimates cleanly).
    """
    existing = (
        db.query(StationDemographics)
        .filter_by(station_id=station.id)
        .first()
    )

    if existing:
        existing.population_estimate = population
        existing.radius_km           = RADIUS_KM
        existing.source              = SOURCE_LABEL
        existing.data_year           = DATA_YEAR
        existing.computed_at         = datetime.now(timezone.utc)
        print(f"    updated  (population={population:,})")
    else:
        db.add(StationDemographics(
            station_id          = station.id,
            population_estimate = population,
            radius_km           = RADIUS_KM,
            source              = SOURCE_LABEL,
            data_year           = DATA_YEAR,
            computed_at         = datetime.now(timezone.utc),
        ))
        print(f"    inserted (population={population:,})")

    db.commit()


# ── Runner ────────────────────────────────────────────────────────────────────

def run() -> None:
    db = SessionLocal()
    try:
        for name, lat, lon in STATIONS:
            print(f"\n  [{name}]")

            station = db.query(Station).filter_by(name=name).first()
            if not station:
                print(f"    SKIP — station not found in DB (run weather fetcher first)")
                continue

            print(f"    querying WorldPop ({RADIUS_KM} km radius) ...", end=" ", flush=True)
            population = _fetch_population(lat, lon)
            _upsert_demographics(db, station, population)

    finally:
        db.close()
