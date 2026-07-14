"""
Flood Guard — Demographics Fetcher Runner
==========================================
Fetches population estimates from WorldPop and stores them in Neon.

Run this once to seed the data, then re-run whenever you want to
refresh the estimates (e.g. after a new WorldPop dataset is released).

Usage (from project root):
    python demographics_fetcher/run.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from demographics_fetcher import fetch_demographics


def main() -> None:
    print("=" * 55)
    print("  Flood Guard — Demographics Fetcher")
    print("=" * 55)

    try:
        fetch_demographics.run()
    except Exception as exc:
        print(f"\n  ERROR: {exc}")
        sys.exit(1)

    print("\n" + "=" * 55)
    print("  Done.")
    print("=" * 55)


if __name__ == "__main__":
    main()
