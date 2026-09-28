from datetime import UTC, date, datetime

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.services.gfs_service import GFSWeatherService
from app.ingestion.imd_ingestion import IMDIngestion
from app.ingestion.satellite_ingestion import MOSDACClient
from app.ingestion.satellite_ingestion import SatelliteWeatherIngestion
from app.core.dependencies import (
    redis_cache,
    weather_repository,
)
from app.services.weather_service import WeatherService
from app.core.config import settings
from app.services.source_fusion import score_sources
from app.flood.providers import PROVIDERS, get_flood_data


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

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Live weather provider is temporarily unavailable. "
                "Please retry shortly."
            ),
        ) from exc

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

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Forecast provider is temporarily unavailable. "
                "Please retry shortly."
            ),
        ) from exc

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

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail="Historical weather provider is temporarily unavailable. Please retry shortly.",
        ) from exc

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
            {
                "id": "imd",
                "name": "India Meteorological Department",
                "type": "official-weather-feed",
                "status": (
                    "active"
                    if settings.IMD_API_URL
                    else "planned"
                ),
            },
            {
                "id": "mosdac",
                "name": "MOSDAC / INSAT",
                "type": "satellite",
                "status": (
                    "active"
                    if settings.MOSDAC_API_URL or settings.MOSDAC_CATALOG_URL
                    else "planned"
                ),
            },
        ]
    }


@router.get("/sources")
async def get_data_sources():
    """Describe the authoritative provider role for each data product."""
    return {
        "products": {
            "current_weather": {"provider": "open-meteo", "status": "active"},
            "hourly_forecast": {"provider": "open-meteo", "status": "active"},
            "daily_forecast": {"provider": "open-meteo", "status": "active"},
            "air_quality": {"provider": "open-meteo", "status": "active"},
            "nwp_models": {
                "provider": "open-meteo",
                "models": settings.OPEN_METEO_NWP_MODELS.split(","),
                "status": "active",
                "direct_grib_parsing": "optional",
            },
            "flood": {
                "providers": [
                    {
                        "id": provider_id,
                        "name": provider["name"],
                        "status": "configured" if provider["url"] else "not_configured",
                    }
                    for provider_id, provider in PROVIDERS.items()
                ],
            },
        },
    }


@router.get("/flood")
async def get_flood_forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    return await get_flood_data(latitude, longitude)


@router.get("/imd")
async def get_imd_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    """Fetch, normalize, cache, and persist configured IMD weather data."""

    ingestion = IMDIngestion(
        repository=weather_repository,
        cache=redis_cache,
    )

    try:
        weather = await ingestion.ingest_weather(
            latitude=latitude,
            longitude=longitude,
        )

        return weather.model_dump(mode="json")

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to retrieve IMD weather data: {exc}",
        ) from exc

    finally:
        await ingestion.close()


@router.get("/satellite")
async def get_satellite_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    """Fetch, normalize, cache, and persist configured MOSDAC data."""

    ingestion = SatelliteWeatherIngestion(
        repository=weather_repository,
        cache=redis_cache,
    )

    try:
        return await ingestion.ingest_live(
            latitude=latitude,
            longitude=longitude,
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to retrieve satellite weather data: {exc}",
        ) from exc

    finally:
        await ingestion.close()


@router.get("/satellite/catalog")
async def get_satellite_catalog():
    """Fetch live INSAT granule metadata from the MOSDAC catalog."""
    client = MOSDACClient()

    try:
        return await client.get_latest_catalog()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to retrieve MOSDAC catalog data: {exc}",
        ) from exc
    finally:
        await client.close()


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
        "provenance": {
            "provider": "NOAA GFS",
            "role": "numerical weather prediction",
            "status": "live",
            **score_sources(["noaa-gfs"]).as_dict(),
        },
    }


@router.get("/gfs/forecast")
async def get_gfs_forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    limit: int = Query(16, ge=1, le=64),
):
    """Return the stored multi-hour NOAA GFS point series, when available."""
    records = await weather_repository.get_gfs_series(
        latitude=latitude,
        longitude=longitude,
        limit=limit,
    )
    latest = None
    if records:
        latest = max(
            datetime.fromisoformat(
                str(record["valid_at"]).replace("Z", "+00:00")
            ).astimezone(UTC)
            for record in records
        )
    is_fresh = latest is not None and (datetime.now(UTC) - latest).total_seconds() <= 48 * 3600
    status = "live" if is_fresh else "stale" if records else "unavailable"
    return {
        "source": "noaa-gfs",
        "status": status,
        "records": records if is_fresh else [],
        "provenance": {
            "provider": "NOAA GFS",
            "role": "numerical weather prediction",
            "status": status,
            **score_sources(
                ["noaa-gfs"],
                retrieved_at=latest,
            ).as_dict(),
        },
        "message": (
            None
            if is_fresh
            else "GFS data exists but is older than 48 hours; waiting for a fresh model ingestion."
            if records
            else "GFS forecast ingestion has not produced data for this location yet."
        ),
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
