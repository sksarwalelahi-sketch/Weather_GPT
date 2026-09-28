# WeatherGPT — Weather Data Platform

WeatherGPT is a conversational AI platform for weather forecasting,
alerts, climate information, and decision support.

## Member 1 — Weather Data & NWP Platform

This component is responsible for:

- Weather data acquisition
- Open-Meteo integration
- NOAA GFS and ECMWF Open Data through Open-Meteo model APIs
- Historical weather data
- Data ingestion
- Data validation
- Data normalization
- MongoDB storage
- Redis caching
- FastAPI weather APIs
- NDMA SACHET, NOAA/NWS, and Open-Meteo Flood alert integration

## Alert and warning sources

The live alerts endpoint uses these source roles:

- NDMA SACHET: official Indian disaster warnings when `NDMA_SACHET_ENABLED=true`
  and `NDMA_SACHET_API_URL` is configured.
- NOAA/NWS: official active weather alerts from `NOAA_ALERTS_API_URL`.
- Open-Meteo Flood API: model-derived river discharge outlooks, explicitly
  marked as non-official and never presented as a government warning.

Configuration:

```env
NDMA_SACHET_ENABLED=true
NDMA_SACHET_API_URL=https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml
NOAA_ALERTS_API_URL=https://api.weather.gov/alerts/active
OPEN_METEO_FLOOD_API_URL=https://flood-api.open-meteo.com/v1/flood
ALERT_PROVIDER_TIMEOUT_SECONDS=10
```

## Project Status

🚧 Under Development

## NWP model strategy

The initial NWP implementation uses Open-Meteo as the API gateway for
`gfs_seamless` (NOAA GFS) and `ecmwf_ifs025` (ECMWF Open Data). This keeps
real-time model access simple and avoids requiring direct GRIB parsing during
normal development and evaluation. Configure the models with:

```env
OPEN_METEO_NWP_MODELS=gfs_seamless,ecmwf_ifs025
```

## Background ingestion workers

Scheduled current-weather and GFS ingestion can run through the bounded
`IngestionWorkerPool`. Configure concurrency and exponential retry behavior
with `INGESTION_WORKER_COUNT`, `INGESTION_MAX_RETRIES`, and
`INGESTION_RETRY_BASE_SECONDS`. After retries are exhausted, failures are
recorded in MongoDB collection `failed_ingestions`.

## Scheduler locations

Configure one or more scheduled locations with semicolon-separated
`latitude,longitude` pairs:

```env
SCHEDULER_LOCATIONS=20.2961,85.8245;28.6139,77.2090
```

Each location receives independent current-weather and forecast jobs.

## API security and operations

Set comma-separated keys to require `X-API-Key` on protected API requests:

```env
API_KEYS=replace-with-a-long-random-key
RATE_LIMIT_PER_MINUTE=120
CORS_ORIGINS=http://localhost:3000,https://app.example.com
```

Requests are logged through the `weathergpt.api` logger. Rate limiting is
in-process; use a shared gateway or Redis-backed limiter for multi-process
or multi-instance deployments.

## Alert store and APIs

Alerts are persisted in MongoDB collection `alerts` with indexed IDs,
status/expiry, location, and creation time fields.

- `POST /alerts` creates and publishes an alert.
- `GET /alerts` queries active alerts by default and supports severity, source,
  coordinates, pagination, and `active_only=false`.
- `GET /alerts/history` queries the complete alert history.
- `GET /alerts/{alert_id}` retrieves one alert.

## Readiness and monitoring

- `GET /health` reports process health.
- `GET /ready` checks MongoDB and Redis connectivity and returns HTTP 503
  when either dependency is unavailable.
- `GET /metrics` returns in-process uptime and counters for HTTP requests,
  ingestion attempts, retries, and terminal failures.
- Application logs are emitted as JSON lines with request method, path, status,
  and duration fields.
- Terminal ingestion failures are persisted in `failed_ingestions` and
  published to `/ws/alerts` as `ingestion_failure` events.

## Technology Stack

- Python
- FastAPI
- Open-Meteo
- NOAA GFS and ECMWF Open Data through Open-Meteo
- MongoDB
- Redis