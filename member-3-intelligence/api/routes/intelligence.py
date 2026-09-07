from fastapi import APIRouter, HTTPException, Query

from services.intelligence_service import IntelligenceService


router = APIRouter(
    prefix="/intelligence",
    tags=["Intelligence"],
)

service = IntelligenceService()


@router.get("/current")
def analyze_current_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    location_name: str | None = None,
):
    try:
        result = service.analyze_current(
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
        )

        return result.model_dump(mode="json")

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to analyze current weather: {exc}",
        ) from exc


@router.get("/forecast")
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

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to analyze forecast weather: {exc}",
        ) from exc