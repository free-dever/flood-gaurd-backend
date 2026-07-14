# Flood Guard — Operations

How the running pieces of this system get refreshed, and how often. See
`docs/the_plan.md` for the original architecture/design doc — this file
covers day-to-day operation instead.

## Scheduled jobs

| Job | Command | Cadence | Why |
|---|---|---|---|
| Weather + predictions | `python run_pipeline.py` | 1-2x/day | Weather data (and therefore predictions) goes stale quickly. Runs the weather fetcher, then — only if that succeeded — the flood prediction job, so predictions are never computed from stale weather data. |
| Demographics | `python demographics_fetcher/run.py` | Manual, ~yearly | Population estimates change far too slowly to justify any automation. Run by hand whenever a new WorldPop dataset year is worth pulling in. |

Nothing above is wired to an actual scheduler yet — for now, both are run
by hand. Once this is deployed (see `docs/the_plan.md`'s Phase 4), the
weather+predictions row becomes a hosting-platform Cron Job pointed at
`run_pipeline.py`; the demographics row stays manual regardless of hosting.

## `run_pipeline.py` behavior

- Runs `weather_fetcher.fetch_weather.run()`, then `model_service.predict_flood_risk.run()`, in that order, in one process.
- If the weather fetch raises, the prediction step is **skipped entirely** — predicting from stale/partial weather data and presenting it as "current" would be misleading. The process exits non-zero either way something failed, so a scheduler can alert on it.
- Both fetchers can also still be run individually (`weather_fetcher/run.py`, `model_service/run.py`) for manual/debugging use — `run_pipeline.py` doesn't replace them, it just chains them for the automated path.

## One-time setup step

New tables (e.g. `flood_predictions`) are created via SQLAlchemy's
`create_all_tables()`, which only adds missing tables — it never alters
existing ones. After pulling schema changes to `shared/database.py`, run:

```
python shared/database.py
```

against whichever Postgres instance you're pointed at (`DATABASE_URL` in
`.env`), once, before running any fetcher/job that depends on the new
table.
