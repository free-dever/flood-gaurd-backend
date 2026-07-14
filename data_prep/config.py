"""
Flood Guard — Data Preparation Configuration
=============================================
All settings for building the ML training dataset.
Adjust FLOOD_THRESHOLD_MM and FLOOD_LOOKAHEAD_H here to experiment
with different labeling strategies without changing the script logic.
"""

import os

# ── Project root (one level above data_prep/) ──────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Training location ─────────────────────────────────────────────────────────────
# We train on Kampala city centre — all 4 stations are within 5 km of
# each other, so one set of weather patterns covers all of them.
STATION_NAME = "kampala_city_centre"
STATION_LAT  = 0.3476
STATION_LON  = 32.5825

# ── Date range ───────────────────────────────────────────────────────────────
# Open-Meteo ERA5 archive starts from 1940 and has a ~5-day lag.
# 2010–2026 gives us ~16 years = 140,000+ hourly records.
TRAIN_START = "2010-01-01"
TRAIN_END   = "2026-06-30"

# ── Flood labeling ────────────────────────────────────────────────────────────
# FLOOD_THRESHOLD_MM: rainfall accumulated over FLOOD_LOOKAHEAD_H hours
# that we define as flood-level precipitation.
# 30 mm / 3 hours is grounded in Uganda Meteorological Authority
# thresholds and published research on Kampala urban flooding.
FLOOD_THRESHOLD_MM = 5.0    # mm accumulated in the lookahead window
                             # ERA5 spatially averages over ~25 km grid cells,
                             # so 5 mm/3 h at ERA5 scale corresponds to roughly
                             # 15–25 mm/3 h of actual local rainfall in Kampala
                             # — the heavy-rain threshold from Uganda Met Authority.
                             # This gives ~2 % positive examples (~2,900 rows),
                             # a workable class balance for the four ML models.
FLOOD_LOOKAHEAD_H  = 3      # hours ahead we’re predicting flood conditions

# ── Output ──────────────────────────────────────────────────────────────────
OUTPUT_PATH = os.path.join(BASE_DIR, "model_service", "datasets", "training_data.csv")

# ── API ─────────────────────────────────────────────────────────────────────
OPENMETEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
REQUEST_TIMEOUT       = 120   # ERA5 pulls can be slow for 16-year windows
