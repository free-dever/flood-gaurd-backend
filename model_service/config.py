"""
Flood Guard — Model Prediction Batch Job Configuration
=========================================================
Edit this file to change which model is served, monitoring stations, or
how much historical context the rolling-window features need.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Monitoring stations ───────────────────────────────────────────────────────
# Kept in sync with weather_fetcher/config.py — same 4 Kampala locations.
# All 4 get predictions, even though the model was trained only on
# kampala_city_centre's weather — the 4 stations are within ~5km of each
# other (see data_prep/config.py), so one weather pattern covers all of them.
STATIONS = [
    ("kampala_city_centre", 0.3476,  32.5825),
    ("nakivubo_channel",    0.3167,  32.5833),
    ("lubigi_wetland",      0.3333,  32.5333),
    ("bwaise",              0.3417,  32.5564),
]

# ── Served model ───────────────────────────────────────────────────────────────
# LightGBM was the best all-around performer across the 4 models compared
# in model_training/train_models.ipynb (highest F1/F2 at its tuned threshold).
MODEL_NAME      = "LightGBM"
MODEL_PATH      = os.path.join(BASE_DIR, "models", "lightgbm.joblib")
THRESHOLDS_PATH = os.path.join(BASE_DIR, "models", "thresholds.json")

# ── Rolling-window context ────────────────────────────────────────────────────
# precip_24h needs a full 24-row window ending at the target hour, i.e. 23
# hours of history before it. Requiring 24 total historical rows covers both
# the "current" row (uses itself + 23 prior) and the first forecast row
# (uses 23 prior historical rows + itself).
MIN_HISTORY_HOURS = 23

# How many trailing historical hours to pull per station as rolling-window
# context. Only ~24h are strictly needed; this is a generous buffer against
# occasional missing/null hours in weather_historical.
HISTORY_LOOKBACK_HOURS = 48
