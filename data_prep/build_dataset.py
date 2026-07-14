"""
Flood Guard — Training Dataset Builder
=======================================
Fetches 16 years of ERA5 hourly weather data for Kampala from the
Open-Meteo archive, engineers rolling-window features, labels each
hour based on whether flood-level rainfall will occur in the next
3 hours, and saves a clean CSV for model training.

What ERA5 is
------------
ERA5 is ECMWF’s global atmospheric reanalysis — it reconstructs
hourly weather going back to 1940 by combining forecast model output
with historical observations. It’s the standard reference dataset
for climate and weather ML research.

Run once from the project root:
    python data_prep/build_dataset.py

Output:
    datasets/training_data.csv
"""

import os
import sys

import pandas as pd
import requests

# Allow imports from the project root (shared/, data_prep/) when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_prep.config import (
    STATION_LAT, STATION_LON,
    TRAIN_START, TRAIN_END,
    FLOOD_THRESHOLD_MM, FLOOD_LOOKAHEAD_H,
    OUTPUT_PATH,
    OPENMETEO_ARCHIVE_URL, REQUEST_TIMEOUT,
)
from shared.features import engineer_rolling_features

# Variables to pull from the ERA5 archive.
# These match exactly what the live weather fetcher stores, so the
# same features are available for both training and inference.
HOURLY_VARS = [
    "precipitation",
    "temperature_2m",
    "wind_speed_10m",
    "relative_humidity_2m",
]


# ── Step 1: Fetch ──────────────────────────────────────────────────────────────────

def fetch_era5() -> pd.DataFrame:
    """
    Pull hourly ERA5 weather from Open-Meteo for the full training window.

    The archive endpoint accepts arbitrary date ranges — no pagination needed.
    Timezone is set to Africa/Kampala so timestamps align with local time.
    """
    params = {
        "latitude":   STATION_LAT,
        "longitude":  STATION_LON,
        "start_date": TRAIN_START,
        "end_date":   TRAIN_END,
        "hourly":     ",".join(HOURLY_VARS),
        "timezone":   "Africa/Kampala",
    }

    print(f"  Fetching ERA5 data  {TRAIN_START} → {TRAIN_END} ...")
    resp = requests.get(OPENMETEO_ARCHIVE_URL, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    hourly = resp.json()["hourly"]

    df = pd.DataFrame({
        "timestamp":             pd.to_datetime(hourly["time"]),
        "precipitation_mm":      hourly["precipitation"],
        "temperature_c":         hourly["temperature_2m"],
        "wind_speed_kmh":        hourly["wind_speed_10m"],
        "relative_humidity_pct": hourly["relative_humidity_2m"],
    })

    print(f"  Fetched {len(df):,} hourly records.")
    return df


# ── Step 2: Feature engineering ────────────────────────────────────────────────────

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add rolling-window precipitation features and the flood label.

    WHY ROLLING WINDOWS?
    --------------------
    Kampala floods because sustained or repeated heavy rain overwhelms
    its drainage system. A single rainy hour is less dangerous than 24
    hours of continuous rain. Rolling sums over multiple time windows
    capture this cumulative effect and give the model richer signal
    than any single point-in-time measurement.

    FEATURE SUMMARY
    ---------------
    precip_3h           — rainfall in past 3 hours (short burst)
    precip_6h           — rainfall in past 6 hours (medium burst)
    precip_12h          — rainfall in past 12 hours (half-day saturation)
    precip_24h          — rainfall in past 24 hours (full-day accumulation)
    max_precip_1h_in_6h — peak 1-hour intensity in the past 6 hours
                           (a 40 mm burst in 1 hour is more dangerous
                           than 40 mm spread evenly over 6 hours)
    relative_humidity   — soil moisture proxy; high humidity before rain
                           means the ground is already saturated
    month               — captures Kampala’s rainy seasons (Mar–May,
                           Oct–Nov) — same rainfall is riskier in season

    FLOOD LABEL (target variable)
    ------------------------------
    flood_label = 1 if the next FLOOD_LOOKAHEAD_H hours will accumulate
                    ≥ FLOOD_THRESHOLD_MM of precipitation
    flood_label = 0 otherwise

    Predicting the FUTURE (not the present) gives the model early-warning
    capability. The model sees current conditions and predicts whether
    flooding is coming, not whether it is already happening.
    """
    # Rolling-window precipitation features + month live in shared/features.py
    # so the training pipeline and the live prediction job (model_service/)
    # compute them identically — any drift between the two would silently
    # skew served predictions relative to what the model was trained on.
    df = engineer_rolling_features(df)
    p = df["precipitation_mm"]  # shorthand alias, still needed for the label below

    # ── Flood label (lookahead) ─────────────────────────────────────────────────────────────
    # rolling(n).sum()    at row i = sum of rows i, i-1, … i-(n-1)  [past]
    # .shift(-n)          shifts the result n positions earlier in the index
    # so the value at row i becomes the rolling sum that was at row i+n
    # = sum of rows i+n, i+n-1, … i+1  [= next n hours from row i]
    future_precip = (
        p.rolling(FLOOD_LOOKAHEAD_H, min_periods=FLOOD_LOOKAHEAD_H)
         .sum()
         .shift(-FLOOD_LOOKAHEAD_H)
    )
    df["flood_label"] = (future_precip >= FLOOD_THRESHOLD_MM).astype(int)

    # ── Drop incomplete rows ────────────────────────────────────────────────────────────────
    # NaN appears in:
    #   first 23 rows — rolling(24) doesn’t have a full window yet
    #   last 3 rows   — future_precip has no data beyond the dataset end
    df = df.dropna().reset_index(drop=True)

    return df


# ── Step 3: Assemble, report, save ────────────────────────────────────────────────────────

def build_dataset() -> pd.DataFrame:
    """
    Orchestrates the full pipeline: fetch → engineer → save.
    Returns the completed DataFrame so callers can inspect it.
    """
    # 1. Fetch raw ERA5
    df = fetch_era5()

    # 2. Add features and label
    print("  Engineering features ...")
    df = engineer_features(df)

    # 3. Keep only the columns the model will use.
    #    timestamp is kept for traceability but won’t be a model feature.
    model_cols = [
        "timestamp",
        "precip_3h",
        "precip_6h",
        "precip_12h",
        "precip_24h",
        "max_precip_1h_in_6h",
        "relative_humidity_pct",
        "month",
        "flood_label",
    ]
    df = df[model_cols]

    # 4. Report class balance.
    #    Class imbalance (many more 0s than 1s) is expected — flood-level
    #    rain is rare. We’ll handle this in training with class_weight=’balanced’.
    n_total    = len(df)
    n_flood    = int(df["flood_label"].sum())
    n_no_flood = n_total - n_flood

    print(f"\n  Dataset summary")
    print(f"    Total hourly rows  : {n_total:,}")
    print(f"    flood_label = 1    : {n_flood:,}  ({100 * n_flood / n_total:.2f}%)")
    print(f"    flood_label = 0    : {n_no_flood:,}  ({100 * n_no_flood / n_total:.2f}%)")
    print(f"    Imbalance ratio    : 1 : {n_no_flood // max(n_flood, 1)}")

    # 5. Save
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n  Saved → {OUTPUT_PATH}")

    return df


if __name__ == "__main__":
    print("=" * 55)
    print("  Flood Guard — Dataset Builder")
    print("=" * 55)
    build_dataset()
    print("\n" + "=" * 55)
    print("  Done.")
    print("=" * 55)
