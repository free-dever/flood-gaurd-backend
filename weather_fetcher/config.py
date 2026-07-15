"""
Flood Guard — Weather Fetcher Configuration
============================================
Edit this file to change monitoring stations, date ranges, or API settings.
No other files need to change for most configuration adjustments.
"""

from datetime import date, timedelta

# ── Monitoring stations ───────────────────────────────────────────────────────
# Format: (name, latitude, longitude)
# All four locations are flood-prone areas in and around Kampala.
STATIONS = [
    ("kampala_city_centre", 0.3476,  32.5825),
    ("nakivubo_channel",    0.3167,  32.5833),
    ("lubigi_wetland",      0.3333,  32.5333),
    ("bwaise",              0.3417,  32.5564),
]

# ── Historical date range ─────────────────────────────────────────────────────
# Open-Meteo archive has a ~1-day lag, so end date is yesterday.
HISTORY_END   = date.today() - timedelta(days=1)
HISTORY_START = HISTORY_END  - timedelta(days=29)   # 30-day rolling window

# ── Forecast horizon ──────────────────────────────────────────────────────────
FORECAST_DAYS = 7    # hourly weather forecast (max 16 on free tier)

# ── API base URLs ─────────────────────────────────────────────────────────────
OPENMETEO_ARCHIVE_URL  = "https://archive-api.open-meteo.com/v1/archive"
OPENMETEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# ── Request settings ──────────────────────────────────────────────────────────
# 60s (not 30s) — GitHub Actions runners have seen slower round-trips to
# Open-Meteo than local dev; 30s cut it too close and caused real failures.
REQUEST_TIMEOUT = 60   # seconds

# This job runs unattended (GitHub Actions, twice a day — see
# .github/workflows/pipeline.yml) with no one around to just retry a
# transient timeout by hand, so failed requests get a few automatic retries
# before giving up.
MAX_RETRIES           = 3
RETRY_BACKOFF_SECONDS = 10

# Both real CI failures so far timed out on a LATER station in the loop
# (never the first), suggesting rapid back-to-back requests may be getting
# throttled/slowed by Open-Meteo rather than pure bad luck. A short pause
# between each station's requests spaces the load out.
INTER_REQUEST_DELAY_SECONDS = 3
