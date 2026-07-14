"""
Flood Guard — Flood Prediction Job Runner
============================================
Runs the trained LightGBM model against current weather data and stores
flood-risk predictions in Neon.

Run this after weather_fetcher/run.py has refreshed weather data —
prediction quality depends on fresh historical + forecast rows.

Usage (from project root):
    python model_service/run.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_service import predict_flood_risk


def main() -> None:
    print("=" * 55)
    print("  Flood Guard — Flood Prediction Job")
    print("=" * 55)

    try:
        predict_flood_risk.run()
    except Exception as exc:
        print(f"\n  ERROR: {exc}")
        sys.exit(1)

    print("\n" + "=" * 55)
    print("  Done.")
    print("=" * 55)


if __name__ == "__main__":
    main()
