"""
Flood Guard — FastAPI Application Entry Point
==============================================
This is where the FastAPI app is created and all routers are registered.

To start the server (from the project root):
    uvicorn fastapi_app.app.main:app --reload

Swagger UI (interactive docs) will be available at:
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI

# ── App instance ──────────────────────────────────────────────────────────────
# This object IS the application. Everything else (routes, middleware) attaches
# to it. The metadata here feeds directly into the Swagger UI.
app = FastAPI(
    title="Flood Guard API",
    description="Weather data API for flood early-warning in Kampala, Uganda.",
    version="0.1.0",
)

# ── Routers ───────────────────────────────────────────────────────────────────
# Each router lives in its own file and handles one group of related endpoints.
# We register them here as they are built.
from fastapi_app.app.routers import stations, weather, demographics, predictions
app.include_router(stations.router)
app.include_router(weather.router)
app.include_router(demographics.router)
app.include_router(predictions.router)


# ── Health endpoint ───────────────────────────────────────────────────────────
# The simplest possible route — no DB, no logic.
# Its only job is to confirm the server is up and reachable.
# This is the first thing a monitoring tool or a frontend will ping.
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
