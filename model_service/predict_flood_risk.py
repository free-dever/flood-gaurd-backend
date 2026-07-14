"""
Flood Guard — Flood Risk Prediction Job
==========================================
Reads weather data for all 4 stations, engineers the same rolling-window
features used in training, runs the trained LightGBM model + its tuned F2
threshold, and writes predictions to flood_predictions.

How it works (per station)
---------------------------
  1. Pull the last HISTORY_LOOKBACK_HOURS hours from weather_historical
     (context only — needed to compute rolling windows for the first
     forecast hours) plus all rows from weather_forecast.
  2. Concatenate into one continuous, time-ordered series and run the
     SAME engineer_rolling_features() used at training time.
  3. Anchor "current" on the first forecast row, not the last historical
     row: weather_fetcher's historical archive has a ~1-day lag
     (HISTORY_END = today - 1), so the freshest real data for "now" lives
     in weather_forecast (which starts today), not at the tail of
     weather_historical. Falling back to the last historical row only
     applies if forecast data isn't available yet for some reason.
  4. Predict probability + apply the tuned threshold for every hour from
     "current" through the end of the forecast horizon.
  5. Replace all existing flood_predictions rows for that station (same
     delete-then-insert pattern weather_forecast already uses).

Stations with insufficient historical rows (e.g. a brand-new station) are
skipped for this run rather than crashing the whole job.
"""

import os
import sys
import json
from datetime import datetime, timezone

import joblib
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database import (
    SessionLocal, Station, WeatherHistorical, WeatherForecast, FloodPrediction,
)
from shared.features import engineer_rolling_features, MODEL_FEATURES
from model_service.config import (
    STATIONS, MODEL_NAME, MODEL_PATH, THRESHOLDS_PATH,
    MIN_HISTORY_HOURS, HISTORY_LOOKBACK_HOURS,
)

_model = None
_threshold = None


# ── Model loading ─────────────────────────────────────────────────────────────

def _load_model():
    """Load the served model + its tuned threshold once, cache module-level."""
    global _model, _threshold
    if _model is None:
        _model = joblib.load(MODEL_PATH)
        with open(THRESHOLDS_PATH) as f:
            thresholds = json.load(f)
        _threshold = thresholds[MODEL_NAME]
    return _model, _threshold


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rows_to_df(rows) -> pd.DataFrame:
    return pd.DataFrame([{
        "timestamp": r.timestamp,
        "precipitation_mm": r.precipitation_mm,
        "relative_humidity_pct": r.relative_humidity_pct,
    } for r in rows])


def _build_prediction_frame(db, station: Station):
    """
    Returns (output_df, current_ts), or None if there isn't enough
    historical context to compute even the "current" prediction.

    output_df has MODEL_FEATURES + timestamp columns and covers exactly
    {current hour} union {forecast hours with complete rolling features}.
    """
    hist_rows = (
        db.query(WeatherHistorical)
        .filter(WeatherHistorical.station_id == station.id)
        .order_by(WeatherHistorical.timestamp.desc())
        .limit(HISTORY_LOOKBACK_HOURS)
        .all()
    )
    hist_rows = list(reversed(hist_rows))  # back to ascending order

    if len(hist_rows) < MIN_HISTORY_HOURS + 1:
        return None

    forecast_rows = (
        db.query(WeatherForecast)
        .filter(WeatherForecast.station_id == station.id)
        .order_by(WeatherForecast.timestamp.asc())
        .all()
    )

    combined = pd.concat(
        [_rows_to_df(hist_rows), _rows_to_df(forecast_rows)], ignore_index=True
    )
    # Guard against any historical/forecast timestamp overlap; forecast wins
    # (it's the fresher fetch).
    combined = combined.drop_duplicates(subset="timestamp", keep="last")
    combined = engineer_rolling_features(combined)  # sorts internally

    if forecast_rows:
        current_ts = forecast_rows[0].timestamp
    else:
        current_ts = hist_rows[-1].timestamp

    output_df = combined[combined["timestamp"] >= current_ts].copy()

    # Drop any hour whose rolling features are incomplete (e.g. a null
    # precipitation/humidity reading upstream) rather than crash the job.
    before = len(output_df)
    output_df = output_df.dropna(subset=MODEL_FEATURES)
    skipped = before - len(output_df)
    if skipped:
        print(f"    ({skipped} hour(s) skipped — incomplete weather data)")

    if output_df.empty:
        return None

    return output_df, current_ts


# ── Prediction + storage ──────────────────────────────────────────────────────

def predict_and_store_for_station(db, station: Station) -> int:
    """Predict + replace flood_predictions rows for one station. Returns row count stored."""
    model, threshold = _load_model()

    result = _build_prediction_frame(db, station)
    if result is None:
        return 0
    output_df, current_ts = result

    X = output_df[MODEL_FEATURES]
    probabilities = model.predict_proba(X)[:, 1]

    db.query(FloodPrediction).filter_by(station_id=station.id).delete()

    now = datetime.now(timezone.utc)
    for ts, prob in zip(output_df["timestamp"], probabilities):
        db.add(FloodPrediction(
            station_id=station.id,
            timestamp=ts,
            flood_probability=float(prob),
            is_flood_risk=bool(prob >= threshold),
            is_current=bool(ts == current_ts),
            model_name=MODEL_NAME,
            model_threshold=threshold,
            predicted_at=now,
        ))
    db.commit()
    return len(output_df)


# ── Runner ────────────────────────────────────────────────────────────────────

def run() -> None:
    _load_model()
    db = SessionLocal()
    try:
        for name, lat, lon in STATIONS:
            print(f"\n  [{name}]")

            station = db.query(Station).filter_by(name=name).first()
            if not station:
                print("    SKIP — station not found in DB (run weather fetcher first)")
                continue

            n = predict_and_store_for_station(db, station)
            if n == 0:
                print(
                    f"    SKIP — insufficient historical context "
                    f"(need >= {MIN_HISTORY_HOURS + 1}h) or no complete hours available"
                )
            else:
                print(f"    {n} rows stored (1 current + {n - 1} forecast)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
