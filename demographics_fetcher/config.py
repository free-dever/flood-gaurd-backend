"""
Flood Guard — Demographics Fetcher Configuration
=================================================
Central config for the WorldPop population fetcher.
Adjust RADIUS_KM to change the flood zone buffer size.
"""

# ── Stations ──────────────────────────────────────────────────────────────────
# Kept in sync with weather_fetcher/config.py — same 4 Kampala locations.
STATIONS = [
    ("kampala_city_centre", 0.3476,  32.5825),
    ("nakivubo_channel",    0.3167,  32.5833),
    ("lubigi_wetland",      0.3333,  32.5333),
    ("bwaise",              0.3417,  32.5564),
]

# ── Buffer radius ─────────────────────────────────────────────────────────────
# The circular area around each station used to sum population.
# 1.0 km is appropriate for Kampala's urban density.
RADIUS_KM: float = 1.0

# ── WorldPop settings ─────────────────────────────────────────────────────────
WORLDPOP_STATS_URL = "https://api.worldpop.org/v1/services/stats"
WORLDPOP_DATASET   = "wpgppop"   # WorldPop Global Population dataset
DATA_YEAR          = 2020        # Latest available census-adjusted year
SOURCE_LABEL       = "worldpop"

# ── Request settings ──────────────────────────────────────────────────────────
REQUEST_TIMEOUT = 60   # WorldPop API can be slow — give it a full minute
CIRCLE_POINTS   = 32  # Number of polygon vertices used to approximate a circle
