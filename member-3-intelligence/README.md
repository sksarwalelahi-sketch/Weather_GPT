# WeatherGPT — Member 3 Intelligence & Decision Engine

Member 3 is the **Intelligence and Decision Engine** of WeatherGPT.

It receives weather data from Member 1, analyzes weather risks and hazards, and exposes REST APIs that can be consumed by Member 4 and other project components.

---

## Architecture

```text
Member 1 — Data & NWP Platform
             |
             | HTTP
             v
Member 3 — Intelligence & Decision Engine
             |
             +-- Risk Assessment
             +-- Hazard Detection
             +-- Alerts
             +-- Advisories
             +-- Forecast Analysis
             +-- Historical Climate Analysis
             |
             v
Member 4 — Mobile / GIS / UX
```

---

## Tech Stack

- Python
- FastAPI
- Pydantic
- Pytest
- Uvicorn

---

## Features

Member 3 currently provides:

- Current weather risk assessment
- Forecast risk analysis
- Historical climate analysis
- Weather hazard detection
- Weather alerts
- Weather advisories
- Confidence scoring
- Data quality assessment
- Member 1 API integration
- REST API for frontend/mobile integration

---

# Getting Started

## 1. Navigate to the project

```powershell
cd member-3-intelligence
```

## 2. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

## 3. Configure Member 1 API

Member 3 obtains weather data from the Member 1 API.

Set the Member 1 API URL using:

```powershell
$env:MEMBER1_API_URL="http://<MEMBER-1-IP>:8000"
```

Example:

```powershell
$env:MEMBER1_API_URL="http://192.168.31.225:8000"
```

If `MEMBER1_API_URL` is not set, Member 3 uses:

```text
http://127.0.0.1:8000
```

## 4. Start Member 3

```powershell
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8001
```

Member 3 will run on:

```text
http://127.0.0.1:8001
```

---

# API Documentation

FastAPI automatically provides interactive API documentation.

## Swagger UI

```text
http://127.0.0.1:8001/docs
```

## ReDoc

```text
http://127.0.0.1:8001/redoc
```

The Swagger interface can be used to test the API endpoints directly from a browser.

---

# Health Check

## Endpoint

```http
GET /health
```

Example:

```text
http://127.0.0.1:8001/health
```

Example response:

```json
{
  "status": "healthy",
  "service": "weathergpt-intelligence",
  "version": "1.0.0"
}
```

---

# Current Weather Intelligence

## Endpoint

```http
GET /api/v1/intelligence/current
```

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `latitude` | float | Yes | Latitude from -90 to 90 |
| `longitude` | float | Yes | Longitude from -180 to 180 |
| `location_name` | string | No | Human-readable location name |

### Example

```text
/api/v1/intelligence/current?latitude=20.281195&longitude=85.843376&location_name=Bhubaneswar
```

### Response

The endpoint returns:

- Location
- Generation timestamp
- Risk assessment
- Hazards
- Alerts
- Advisories
- Climate analysis
- Processing version

The risk assessment includes:

- Overall risk level
- Overall risk score
- Risk components
- Confidence
- Data quality
- Timestamp

---

# Forecast Intelligence

## Endpoint

```http
GET /api/v1/intelligence/forecast
```

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `latitude` | float | Yes | Latitude from -90 to 90 |
| `longitude` | float | Yes | Longitude from -180 to 180 |
| `forecast_days` | integer | Yes | Forecast period from 1 to 16 days |
| `location_name` | string | No | Human-readable location name |

### Example

```text
/api/v1/intelligence/forecast?latitude=20.281195&longitude=85.843376&forecast_days=7&location_name=Bhubaneswar
```

### Response

The endpoint returns:

- Forecast start
- Forecast end
- Forecast points
- Maximum risk level
- Maximum risk score
- Detected hazards
- Summary
- Confidence
- Data source
- Number of data points

Each forecast point contains:

- Weather data
- Risk assessment
- Detected hazards

---

# Historical Climate Intelligence

## Endpoint

```http
GET /api/v1/intelligence/historical
```

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `latitude` | float | Yes | Latitude from -90 to 90 |
| `longitude` | float | Yes | Longitude from -180 to 180 |
| `start_date` | date | Yes | Historical period start |
| `end_date` | date | Yes | Historical period end |
| `baselines` | JSON string | Yes | Climate baseline values |
| `location_name` | string | No | Human-readable location name |

### Supported baseline metrics

```text
temperature
rainfall
wind_speed
```

### Example baseline

```json
{
  "temperature": 30,
  "rainfall": 5,
  "wind_speed": 15
}
```

### Example request

```text
/api/v1/intelligence/historical?latitude=20.281195&longitude=85.843376&start_date=2026-08-18&end_date=2026-08-20&baselines=%7B%22temperature%22%3A30%2C%22rainfall%22%3A5%2C%22wind_speed%22%3A15%7D&location_name=Bhubaneswar
```

### Historical analysis provides

- Average value
- Baseline value
- Anomaly
- Trend
- Trend percentage
- Confidence
- Number of data points

---

# Intelligence Capabilities

## Risk Assessment

The intelligence engine evaluates available weather measurements and generates:

- Overall risk level
- Overall risk score
- Component-level risk
- Confidence
- Data quality

## Hazard Detection

Supported hazard categories include:

- Heavy rain
- Heatwave
- Extreme wind
- Cyclone-related conditions
- Flood-related conditions

## Alerts

The system generates structured alerts when supported risk or hazard conditions are detected.

## Advisories

The system generates domain-oriented recommendations based on detected weather conditions.

## Forecast Analysis

Multiple forecast points are analyzed to determine:

- Maximum risk
- Maximum risk score
- Forecast hazards
- Confidence
- Forecast summary

## Historical Climate Analysis

Historical weather observations are compared with caller-provided baselines to calculate:

- Anomalies
- Trends
- Trend percentages
- Confidence

---

# Member 1 Integration

Member 3 communicates with Member 1 through HTTP.

The Member 1 API provides weather data that is converted by the Member 3 adapter layer into the internal weather models used by the intelligence engine.

### Member 1 endpoints used by Member 3

```text
GET /weather/current
GET /weather/forecast
GET /weather/historical
```

### Configuration

```powershell
$env:MEMBER1_API_URL="http://<MEMBER-1-IP>:8000"
```

Example:

```powershell
$env:MEMBER1_API_URL="http://192.168.31.225:8000"
```

Member 3 does **not** fabricate unavailable weather fields.

If a field is not provided by Member 1, that field remains unavailable to the intelligence engine.

---

# API Error Handling

| Status Code | Meaning |
|---|---|
| `200` | Request processed successfully |
| `422` | Invalid request parameters or baseline data |
| `502` | Member 1 weather API failure |
| `500` | Unexpected internal intelligence error |

---

# Testing

Run the complete test suite:

```powershell
pytest -q
```

Current test status:

```text
172 passed
```

Run the intelligence API tests:

```powershell
pytest -q tests/test_api_intelligence.py
```

Run the historical API tests:

```powershell
pytest -q tests/test_api_historical.py
```

Check for whitespace and patch errors:

```powershell
git diff --check
```

---

# Project Structure

```text
member-3-intelligence/
│
├── api/
│   ├── __init__.py
│   ├── main.py
│   └── routes/
│       ├── __init__.py
│       └── intelligence.py
│
├── intelligence/
│   ├── forecast.py
│   └── decision.py
│
├── integration/
│   ├── member1_adapter.py
│   └── member1_client.py
│
├── schemas/
│   ├── forecast.py
│   └── intelligence.py
│
├── services/
│   └── intelligence_service.py
│
├── tests/
│   ├── test_api_intelligence.py
│   ├── test_api_historical.py
│   ├── test_forecast.py
│   ├── test_decision.py
│   ├── test_intelligence_service.py
│   └── ...
│
├── requirements.txt
├── pytest.ini
└── README.md
```

---

# Member 4 Integration

Member 4 should communicate with Member 3 through the REST API rather than importing Member 3 Python modules directly.

Recommended flow:

```text
Mobile / GIS Application
          |
          | HTTP
          v
Member 3 Intelligence API
          |
          v
Structured Intelligence Result
          |
          +-- Risk
          +-- Hazards
          +-- Alerts
          +-- Advisories
          +-- Forecast
          +-- Climate Analysis
```

When both machines are connected to the same network, Member 4 can access the Member 3 Swagger documentation using:

```text
http://<MEMBER-3-IP>:8001/docs
```

---

# Development Status

Member 3 currently includes:

- Current weather intelligence
- Forecast intelligence
- Historical climate intelligence
- Risk assessment
- Hazard detection
- Alerts
- Advisories
- Member 1 API integration
- FastAPI REST endpoints
- Request validation
- API error handling
- Automated tests
- Live integration verification

Current automated test status:

```text
172 passed
```

---

# API Version

```text
WeatherGPT Intelligence API
Version: 1.0.0
```