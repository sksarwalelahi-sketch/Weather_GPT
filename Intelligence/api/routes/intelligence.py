import json
from datetime import date

from fastapi import APIRouter, HTTPException, Query

from integration.member1_client import Member1APIError
from schemas.forecast import ForecastAnalysis
from schemas.intelligence import WeatherIntelligenceResult
from services.intelligence_service import IntelligenceService


router = APIRouter(
    prefix="/intelligence",
    tags=["Intelligence"],
)

service = IntelligenceService()


@router.get(
    "/current",
    response_model=WeatherIntelligenceResult,
)
def analyze_current_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    location_name: str | None = None,
    source: str = Query(
        "open-meteo",
        pattern="^open-meteo$",
    ),
):
    try:
        arguments = {
            "latitude": latitude,
            "longitude": longitude,
            "location_name": location_name,
        }
        if source != "open-meteo":
            arguments["source"] = source

        result = service.analyze_current(**arguments)

        return result.model_dump(mode="json")

    except Member1APIError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to analyze current weather: {exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Internal intelligence error: {exc}",
        ) from exc


@router.get(
    "/forecast",
    response_model=ForecastAnalysis,
)
def analyze_forecast_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    forecast_days: int = Query(..., ge=1, le=16),
    location_name: str | None = None,
):
    try:
        result = service.analyze_forecast(
            latitude=latitude,
            longitude=longitude,
            forecast_days=forecast_days,
            location_name=location_name,
        )

        return result.model_dump(mode="json")

    except Member1APIError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to analyze forecast weather: {exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Internal intelligence error: {exc}",
        ) from exc


@router.get("/flood")
def get_flood_data(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    """Return source-labelled NOAA, ECMWF, and DWD flood data."""
    try:
        return service.client.get_flood(latitude, longitude)
    except Member1APIError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to retrieve flood data: {exc}",
        ) from exc


@router.get(
    "/historical",
    response_model=WeatherIntelligenceResult,
)
def analyze_historical_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    start_date: date = Query(...),
    end_date: date = Query(...),
    baselines: str = Query(...),
    location_name: str | None = None,
):
    if start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must be before or equal to end_date",
        )

    try:
        parsed_baselines = json.loads(baselines)

        if not isinstance(parsed_baselines, dict):
            raise ValueError("baselines must be a JSON object")

        allowed_metrics = {
            "temperature",
            "rainfall",
            "wind_speed",
        }

        invalid_metrics = set(parsed_baselines) - allowed_metrics

        if invalid_metrics:
            raise ValueError(
                f"Unsupported baseline metrics: "
                f"{', '.join(sorted(invalid_metrics))}"
            )

        for metric in allowed_metrics:
            if metric in parsed_baselines:
                value = parsed_baselines[metric]

                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    raise ValueError(
                        f"Baseline '{metric}' must be numeric"
                    )

        if not parsed_baselines:
            raise ValueError(
                "At least one climate baseline is required"
            )

        result = service.analyze_current_with_history(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            baselines=parsed_baselines,
            location_name=location_name,
        )

        return result.model_dump(mode="json")

    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=422,
            detail="baselines must be valid JSON",
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Member1APIError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to analyze historical weather: {exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Internal intelligence error: {exc}",
        ) from exc