from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.services.gfs_service import GFSWeatherService
from app.core.dependencies import (
    redis_cache,
    weather_repository,
)
from app.services.weather_service import WeatherService


router = APIRouter(
    prefix="/weather",
    tags=["Weather"],
)


def create_weather_service() -> WeatherService:
    return WeatherService(
        repository=weather_repository,
        cache=redis_cache,
    )


def create_gfs_service() -> GFSWeatherService:
    return GFSWeatherService(
        repository=weather_repository,
        cache=redis_cache,
    )


@router.get("/current")
async def get_current_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    service = create_weather_service()

    try:
        weather = await service.get_current_weather(
            latitude=latitude,
            longitude=longitude,
        )

        return weather.model_dump(mode="json")

    finally:
        await service.close()


@router.get("/forecast")
async def get_weather_forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    forecast_days: int = Query(
        7,
        ge=1,
        le=16,
    ),
):
    service = create_weather_service()

    try:
        forecast = await service.get_forecast(
            latitude=latitude,
            longitude=longitude,
            forecast_days=forecast_days,
        )

        return forecast.model_dump(mode="json")

    finally:
        await service.close()


@router.get("/historical")
async def get_historical_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    start_date: date = Query(...),
    end_date: date = Query(...),
):
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail=(
                "start_date must be before "
                "or equal to end_date"
            ),
        )

    service = create_weather_service()

    try:
        historical = await service.get_historical(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        return historical.model_dump(mode="json")

    finally:
        await service.close()


@router.get("/models")
async def get_weather_models():
    """
    Return the weather data and NWP sources
    supported by the WeatherGPT data platform.
    """

    return {
        "models": [
            {
                "id": "open-meteo",
                "name": "Open-Meteo",
                "type": "weather-api",
                "status": "active",
            },
            {
                "id": "noaa-gfs",
                "name": "NOAA GFS",
                "type": "nwp",
                "status": "active",
            },
            {
                "id": "era5",
                "name": "ERA5",
                "type": "historical",
                "status": "active",
            },
        ]
    }

@router.get("/gfs")
async def get_gfs_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    service = create_gfs_service()

    result = await service.get_latest(
        latitude=latitude,
        longitude=longitude,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No GFS data is currently available for this location.",
        )

    # MongoDB's internal ObjectId is not JSON serializable.
    result.pop("_id", None)

    return {
        "source": "noaa-gfs",
        "data": result,
    }


@router.get("/era5")
async def get_era5_weather(
    latitude: float = Query(
        ...,
        ge=-90,
        le=90,
    ),
    longitude: float = Query(
        ...,
        ge=-180,
        le=180,
    ),
):
    """
    Return the latest already-ingested ERA5
    weather data for a location.
    """

    result = await weather_repository.get_latest_era5(
        latitude=latitude,
        longitude=longitude,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No ERA5 data is currently available "
                "for this location."
            ),
        )

    result.pop("_id", None)

    return {
        "source": "era5",
        "data": result,
    }