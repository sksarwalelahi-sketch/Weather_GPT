# WeatherGPT

WeatherGPT is a real-time weather intelligence platform. It combines live
weather ingestion, persistent storage and caching, explainable risk analysis,
an LLM gateway, and a responsive web UI with maps and multilingual voice input.

## Architecture

```text
                         +----------------------+
                         | Frontend             |
                         | Next.js + Leaflet    |
                         | Chat + maps + voice  |
                         +----------+-----------+
                                    |
                         browser/API proxy routes
                                    |
       +----------------------------+----------------------------+
       |                            |                            |
       v                            v                            v
 +-------------+             +-------------+              +-------------+
 | M2 / LLM    | ----------> | M1 / Data   |              | M3 / Intel  |
 | :8002       |             | :8000       | <------------| :8001       |
 | /ask        |             | FastAPI     |   weather    | risk/alerts |
 +-------------+             +------+------+              +-------------+
                                      |
                              +-------+-------+
                              | MongoDB       |
                              | Redis         |
                              +---------------+
```

### Services

| Service | Directory | Default URL | Responsibility |
|---|---|---|---|
| M1 Data | `Data` | `http://127.0.0.1:8000` | Ingestion, normalization, weather APIs, alerts, WebSockets, MongoDB and Redis |
| M3 Intelligence | `Intelligence` | `http://127.0.0.1:8001` | Risk, hazards, advisories, source-aware intelligence |
| M2 LLM gateway | `LLM` | `http://127.0.0.1:8002` | Natural-language analysis, orchestration of M1/M3, and multilingual voice transcription |
| Web frontend | `Frontend` | `http://127.0.0.1:3000` | Mobile-responsive dashboard, chat, map and voice UI |

## Prerequisites

- Windows PowerShell
- Python 3.14 (the project virtual environment is `.venv`)
- Node.js and npm
- Docker Desktop with the Linux engine running
- MongoDB:
  - MongoDB Atlas is supported, or
  - a local MongoDB server on port `27017`
- Ollama is optional for local LLM functionality; deterministic gateway
  behavior still requires the configured M2 dependencies

## First-time setup

From the repository root:

```powershell
cd C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI

.\.venv\Scripts\python.exe -m pip install -r Data\requirements.txt
.\.venv\Scripts\python.exe -m pip install -r Intelligence\requirements.txt
.\.venv\Scripts\python.exe -m pip install -r LLM\requirements.txt

cd Frontend
npm install
cd ..
```

The frontend uses npm scripts from `Frontend/package.json`. M1, M2, and M3 use
the shared `.venv`; direct GRIB parsing is not required for the core NWP path.

## Infrastructure

### Redis

Start Docker Desktop, wait for **Engine running**, then run:

```powershell
docker run -d --name weathergpt-redis -p 6379:6379 redis:7-alpine
```

If the container already exists:

```powershell
docker start weathergpt-redis
```

Verify it:

```powershell
docker exec weathergpt-redis redis-cli ping
# PONG
```

### MongoDB

Configure MongoDB in `Data\.env`. Do not commit credentials.

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=weathergpt
MONGODB_SERVER_SELECTION_TIMEOUT_MS=15000
MONGODB_STARTUP_RETRIES=3
MONGODB_STARTUP_RETRY_DELAY_SECONDS=5
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
```

For Atlas, use the complete `mongodb+srv://...` URI. M1 performs a MongoDB
ping and retries startup before creating indexes. The readiness endpoint checks
both MongoDB and Redis. If startup still fails with `ReplicaSetNoPrimary`,
the Atlas cluster must be resumed/repaired or its Network Access allowlist
must be updated; changing the frontend cannot resolve that database condition.

### Weather data source roles

Open-Meteo is the operational source for current weather, hourly forecast,
daily forecast, and air quality. It also provides the initial NWP access layer
for NOAA GFS (`gfs_seamless`) and ECMWF Open Data (`ecmwf_ifs025`). Direct GRIB
parsing is optional and not required for the core NWP requirement. Flood data is routed through configurable
NOAA National Water Model, ECMWF EFAS, and DWD Open Data adapters:

```env
NOAA_FLOOD_API_URL=
ECMWF_FLOOD_API_URL=
DWD_FLOOD_API_URL=
FLOOD_PROVIDER_TIMEOUT_SECONDS=10
```

For alerts and warnings, M1 consumes NDMA SACHET (when configured), NOAA/NWS
active weather alerts, and Open-Meteo Flood API river-discharge outlooks.
NDMA and NOAA entries are official provider warnings; Open-Meteo flood entries
are model-derived outlooks and are explicitly marked non-official.

```env
NDMA_SACHET_ENABLED=true
NDMA_SACHET_API_URL=https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml
NOAA_ALERTS_API_URL=https://api.weather.gov/alerts/active
OPEN_METEO_FLOOD_API_URL=https://flood-api.open-meteo.com/v1/flood
ALERT_PROVIDER_TIMEOUT_SECONDS=10
```

The flood adapters return `not_configured` until a provider endpoint is set;
the application never labels missing or unverified flood data as live.

### Methodology

WeatherGPT first retrieves location-specific observations and forecasts through
the M1 data service, which validates, normalizes, caches, and records provider
provenance before the Intelligence and LLM services use the results. Open-Meteo
supplies the operational weather and air-quality data, while NOAA GFS and ECMWF
model data provide the initial NWP context. Alert feeds remain source-labelled:
NDMA SACHET and NOAA/NWS warnings are treated as official provider alerts,
whereas Open-Meteo flood values and WeatherGPT risk calculations are presented
as non-official decision support. This separation helps users distinguish
observations, forecasts, model outlooks, derived intelligence, and government
warnings.

## Configuration

Create or update `Data\.env`:

```env
# Persistence and cache
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=weathergpt
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0

# Scheduler locations: semicolon-separated latitude,longitude pairs
SCHEDULER_LOCATIONS=20.2961,85.8245;28.6139,77.2090

# Background ingestion
INGESTION_WORKER_COUNT=4
INGESTION_MAX_RETRIES=3
INGESTION_RETRY_BASE_SECONDS=1

# Optional API protection
API_KEYS=
RATE_LIMIT_PER_MINUTE=120
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

INTELLIGENCE_API_URL=http://127.0.0.1:8001

# NWP and alert providers
OPEN_METEO_NWP_MODELS=gfs_seamless,ecmwf_ifs025
NDMA_SACHET_ENABLED=false
NDMA_SACHET_API_URL=
NOAA_ALERTS_API_URL=https://api.weather.gov/alerts/active
OPEN_METEO_FLOOD_API_URL=https://flood-api.open-meteo.com/v1/flood
ALERT_PROVIDER_TIMEOUT_SECONDS=10
```

When `API_KEYS` is non-empty, protected requests require:

```http
X-API-Key: your-key
```

M2 and M3 use these environment variables:

```powershell
$env:MEMBER1_API_URL = "http://127.0.0.1:8000"
$env:MEMBER3_API_URL = "http://127.0.0.1:8001"
```

The frontend defaults to its Next.js proxy routes. For a deployed setup,
override them with:

```env
NEXT_PUBLIC_M1_URL=https://data.example.com
NEXT_PUBLIC_M2_URL=https://llm.example.com
NEXT_PUBLIC_M3_URL=https://intelligence.example.com
```

## Start the complete application

Start services in this order. Use one PowerShell terminal per service.

### One-command startup

After completing first-time setup, run this single command from the repository
root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start-weathergpt.ps1
```

The launcher starts Redis, M1, M3, M2, and the frontend, waits for all service
health checks, and opens `http://127.0.0.1:3000` in the default browser.
Services run in the background so the terminal remains available. Stop them
with:

```powershell
.\stop-weathergpt.ps1
```

Use the manual commands below when you need separate service logs or want to
debug one service.

### Terminal 1: M1 Data

```powershell
cd C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI\Data
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

If PowerShell treats the spaced path above literally, use the canonical form:

```powershell
cd C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI\Data
C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: M3 Intelligence

```powershell
cd C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI\Intelligence
$env:MEMBER1_API_URL = "http://127.0.0.1:8000"
C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI\.venv\Scripts\python.exe -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8001
```

### Terminal 3: M2 LLM gateway

```powershell
cd C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI\LLM
$env:MEMBER1_API_URL = "http://127.0.0.1:8000"
$env:MEMBER3_API_URL = "http://127.0.0.1:8001"
C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI\.venv\Scripts\python.exe -m uvicorn app.api:app --reload --host 0.0.0.0 --port 8002
```

### Terminal 4: Frontend

```powershell
cd C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI\Frontend
npm run dev
```

Open `http://127.0.0.1:3000`.

For production frontend validation:

```powershell
cd C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI\Frontend
npm run build
npm run start -- -p 3000
```

## Verify the installation

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/ready
Invoke-RestMethod http://127.0.0.1:8001/health
Invoke-RestMethod http://127.0.0.1:8002/
Invoke-RestMethod "http://127.0.0.1:8000/weather/current?latitude=20.2961&longitude=85.8245"
```

Expected M1 readiness response:

```json
{
  "status": "ready",
  "service": "weather-data-platform",
  "checks": {
    "mongodb": "ready",
    "redis": "ready"
  }
}
```

## Main API surface

### M1 Data

- `GET /weather/current?latitude=...&longitude=...`
- `GET /weather/forecast?latitude=...&longitude=...&forecast_days=7`
- `GET /weather/historical?...`
- `GET /weather/sources`
- `GET /weather/flood?latitude=...&longitude=...`
- `POST /alerts`
- `GET /alerts/live?latitude=...&longitude=...`
- `GET /alerts`
- `GET /alerts/history`
- `GET /alerts/{alert_id}`
- `GET /health`
- `GET /ready`
- `GET /metrics`
- `WS /ws/weather?latitude=...&longitude=...`
- `WS /ws/alerts`
- `WS /ws/map`

### M3 Intelligence

The current intelligence endpoint is:

```text
GET /api/v1/intelligence/current
  ?latitude=20.2961
  &longitude=85.8245
  &location_name=Bhubaneswar
  &source=open-meteo
```

Current intelligence uses the canonical Open-Meteo data contract.

Other endpoints:

- `GET /api/v1/intelligence/forecast`
- `GET /api/v1/intelligence/historical`
- `GET /health`

### M2 LLM gateway

- `POST /ask`
- `GET /weather/current`
- `GET /weather/forecast`
- `GET /weather/historical`
- `GET /map/weather/current`
- `GET /map/intelligence/current`
- `GET /locations/search`
- `GET /locations/reverse`
- `GET /docs`

Example:

```powershell
$body = @{ question = "What is the current weather and risk for Bhubaneswar?" } |
  ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8002/ask `
  -Method Post -ContentType "application/json" -Body $body
```

## Data and real-time features

- Open-Meteo current, forecast, air-quality, and historical ingestion
- NOAA GFS and ECMWF model access through Open-Meteo
- NDMA SACHET and NOAA/NWS alert feeds when configured
- Open-Meteo Flood API river-discharge outlooks
- MongoDB collections for weather, alerts, and failed ingestions
- Redis weather caching
- Bounded ingestion workers with exponential retries
- Dynamic scheduler locations
- Alert history and active-alert queries
- WebSocket weather, alert, and map channels
- JSON structured logs, readiness checks, and in-process metrics
- Frontend live weather cards and map refresh
- Browser speech recognition and speech synthesis in chat

## Frontend behavior

The frontend is a Next.js app using React, Tailwind CSS, Leaflet, and
React-Leaflet.

- `/api/m1/*`, `/api/m2/*`, and `/api/m3/*` proxy to local backend services
- Chat sends questions to M2 `/ask`
- Current weather requests M1 and refreshes periodically
- Map station markers request live M1 weather
- Voice input requires a browser supporting Web Speech API
- Voice output uses the browser's speech synthesis engine
- Map tiles come from OpenStreetMap

## Testing

Run M1 tests:

```powershell
cd C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI\Data
..\.venv\Scripts\python.exe -m pytest tests -q
```

Use the canonical executable form if needed:

```powershell
C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI\.venv\Scripts\python.exe -m pytest tests -q
```

Run M3 tests:

```powershell
cd C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI\Intelligence
C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI\.venv\Scripts\python.exe -m pytest tests -q
```

Run the M2 script-style tests:

```powershell
cd C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI\LLM
$env:PYTHONIOENCODING = "utf-8"
C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI\.venv\Scripts\python.exe test_multilingual.py
C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI\.venv\Scripts\python.exe test_regression.py
C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI\.venv\Scripts\python.exe test_ai_pipeline.py
```

Build the frontend:

```powershell
cd C:\Users\Ritik\OneDrive\Desktop\WeatherGPT-AI\Frontend
npm run build
```

## Operations and troubleshooting

### M1 returns `503` from `/ready`

Check both dependencies:

```powershell
docker exec weathergpt-redis redis-cli ping
Test-NetConnection 127.0.0.1 -Port 27017
```

Then verify `Data\.env` values and restart M1.

### Frontend shows fallback data

Confirm all three backend services are running and check the browser Network
panel for `/api/m1`, `/api/m2`, and `/api/m3` responses. In a deployed
environment, set the `NEXT_PUBLIC_*_URL` variables and configure CORS.

### Multilingual voice transcription

Voice input records audio in the browser and transcribes it with the M2
`faster-whisper` service. Use a current browser over HTTPS or localhost and
grant microphone permission. Install `LLM\requirements.txt` before starting
M2; the default `small` speech model downloads the first time voice
transcription is used, so that first request can take longer.

## Documentation

- [M1 Data README](Data/README.md)
- [M3 Intelligence README](Intelligence/README.md)
- [Frontend package](Frontend/package.json)
