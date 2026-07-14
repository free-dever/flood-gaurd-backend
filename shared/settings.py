"""
Flood Guard — Shared Settings
==============================
Reads configuration from the .env file at the project root.
All other modules should import from here rather than calling
os.environ or python-dotenv directly.
"""

import os
from dotenv import load_dotenv

# Resolve project root (one level above this shared/ directory)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_BASE_DIR, ".env"))


def _require(key: str) -> str:
    """Return the value of a required env variable or raise a clear error."""
    value = os.getenv(key)
    if not value:
        raise RuntimeError(
            f"Required environment variable '{key}' is not set. "
            "Check your .env file."
        )
    return value


# ── Required settings ─────────────────────────────────────────────────────────
DATABASE_URL: str = _require("DATABASE_URL")
