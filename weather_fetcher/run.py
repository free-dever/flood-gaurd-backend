"""
Flood Guard — Weather Fetcher Runner
======================================
Fetches weather data from Open-Meteo and persists it to PostgreSQL (Neon).

Usage (from project root):
    python weather_fetcher/run.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weather_fetcher import fetch_weather


def main() -> None:
    print("=" * 55)
    print("  Flood Guard — Weather Fetcher")
    print("=" * 55)

    try:
        fetch_weather.run()
    except Exception as exc:
        print(f"\n  ERROR: {exc}")
        sys.exit(1)

    print("\n" + "=" * 55)
    print("  Done.")
    print("=" * 55)


if __name__ == "__main__":
    main()

