"""
Flood Guard — Daily Pipeline Runner
======================================
Runs the weather fetcher, then (only if that succeeded) the flood
prediction job, in one shot. This is the single entrypoint a scheduler
should invoke — locally via a scheduled task, and later via a Render Cron
Job once this is deployed.

Order matters: predictions are computed from whatever is currently stored
in weather_historical/weather_forecast, so stale weather data means stale
predictions. Running the prediction job is skipped entirely if the weather
fetch fails, rather than predicting from stale data and calling it current.

Intended cadence
-----------------
  run_pipeline.py              — 1-2x/day (weather + predictions together)
  demographics_fetcher/run.py  — manual, roughly yearly (population data
                                  changes far too slowly to justify any
                                  automation)

Usage (from project root):
    python run_pipeline.py
"""

import sys

from weather_fetcher import fetch_weather
from model_service import predict_flood_risk


def main() -> None:
    print("=" * 55)
    print("  Flood Guard — Daily Pipeline")
    print("=" * 55)

    print("\n[1/2] Weather fetch")
    try:
        fetch_weather.run()
    except Exception as exc:
        print(f"\n  ERROR: weather fetch failed: {exc}")
        print("  Skipping prediction job — refusing to predict from stale data.")
        sys.exit(1)

    print("\n[2/2] Flood prediction")
    try:
        predict_flood_risk.run()
    except Exception as exc:
        print(f"\n  ERROR: prediction job failed: {exc}")
        sys.exit(1)

    print("\n" + "=" * 55)
    print("  Pipeline complete.")
    print("=" * 55)


if __name__ == "__main__":
    main()
