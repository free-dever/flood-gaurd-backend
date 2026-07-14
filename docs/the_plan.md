# Flood Guard Backend – Phase 1

## Objective

Build the backend foundation that:

1. Collects weather data from Open-Meteo
2. Stores weather data in PostgreSQL (Neon)
3. Exposes weather data through FastAPI
4. Verifies end-to-end data flow

No machine learning or frontend work is included in this phase.

---

# Phase 1 Architecture

```text
               Open-Meteo
                    │
                    ▼
         Weather Fetcher Service
                    │
                    ▼
             Neon PostgreSQL
                    ▲
                    │
                 FastAPI
                    ▲
                    │
           Swagger / Postman
```

---

# Components

## Weather Fetcher

Responsibilities:

- Fetch historical weather data
- Fetch forecast weather data
- Store weather records in PostgreSQL

Does NOT:

- Serve APIs
- Generate predictions

---

## PostgreSQL (Neon)

Acts as the system source of truth.

Stores:

- Stations
- Historical weather
- Forecast weather

---

## FastAPI

Acts as the backend gateway.

Responsibilities:

- Read data from PostgreSQL
- Expose REST endpoints

Does NOT:

- Fetch Open-Meteo data
- Run ML models

---

# FastAPI Endpoints

## Health

### GET /health

Response:

```json
{
  "status": "ok"
}
```

---

## Stations

### GET /stations

Returns all monitored locations.

Response:

```json
[
  {
    "id": "...",
    "name": "kampala_city_centre",
    "latitude": 0.3476,
    "longitude": 32.5825
  }
]
```

---

## Current Weather

### GET /weather/{station_id}

Returns latest weather observation.

---

## Historical Weather

### GET /weather/{station_id}/history

Query Parameters:

- start_date
- end_date

Example:

GET /weather/1/history?start_date=2026-06-01&end_date=2026-06-15

---

## Forecast Weather

### GET /weather/{station_id}/forecast

Returns forecast records.

---

# Repository Structure

```text
flood_guard/
│
├── fastapi_app/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── services/
│   │   ├── schemas/
│   │   └── db/
|   |
|   └── api_docs/
│
├── weather_fetcher/
│   ├── fetch_weather.py
│   └── config.py
│
├── shared/
│   ├── database.py
│   └── settings.py
│
├── docs/
│ 
|  └── the_plan.md
|
|
├──.gitignore
|
|
├──.env
|
|
└── .venv
```

---

# Development Strategy

## Database

Use Neon PostgreSQL from Day 1.

Local services connect directly to Neon.

Benefits:

- No migration later
- Same environment in development and production
- Simpler setup

---

# Milestone 1 – Database Foundation

Deliverables:

- Neon project created
- Database connection established
- Stations table created
- Weather table created

Success Criteria:

- Weather records can be inserted and queried

---

# Milestone 2 – Weather Fetcher

Deliverables:

- Historical weather ingestion
- Forecast weather ingestion
- Database persistence

Success Criteria:

Open-Meteo → PostgreSQL pipeline operational

---

# Milestone 3 – FastAPI

Deliverables:

- FastAPI scaffold
- Database integration
- Health endpoint
- Station endpoint
- Weather endpoint
- Forecast endpoint

Success Criteria:

FastAPI successfully serves weather data from PostgreSQL

---

# Milestone 4 – Integration Testing

End-to-end verification:

Open-Meteo
→ Weather Fetcher
→ PostgreSQL
→ FastAPI

Success Criteria:

- Weather records stored
- API returns expected responses
- Swagger documentation operational

---

# Future Phases

Phase 2:

- Prediction Service
- Feature Engineering
- Flood Risk Model

Phase 3:

- Frontend Application
- Maps
- Alerts
- Dashboards

Phase 4:

- Containerization
- Deployment
- Monitoring