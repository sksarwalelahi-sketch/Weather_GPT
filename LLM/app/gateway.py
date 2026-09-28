"""
WeatherGPT API Gateway routes.

The gateway keeps the public API in one place while M1 remains the
weather-data service and M3 remains the intelligence service.
"""

import os

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.location.gis import reverse_geocode, search_locations


router = APIRouter()

MEMBER1_API_URL = os.getenv(
    "MEMBER1_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

MEMBER3_API_URL = os.getenv(
    "MEMBER3_API_URL",
    "http://127.0.0.1:8001",
).rstrip("/")


@router.get("/locations/search", tags=["Location"])
def search_location(
    query: str = Query(..., min_length=1),
    count: int = Query(10, ge=1, le=20),
):
    return {"locations": search_locations(query, count)}


@router.get("/locations/reverse", tags=["Location"])
def reverse_location(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    return reverse_geocode(latitude, longitude)


async def _forward_get(
    base_url: str,
    endpoint: str,
    params: dict,
):
    """Forward a GET request to one WeatherGPT backend service."""

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{base_url}{endpoint}",
                params=params,
            )

    except httpx.RequestError as error:
        raise HTTPException(
            status_code=502,
            detail=f"Backend service is unavailable: {error}",
        ) from error

    try:
        data = response.json()
    except ValueError:
        data = {"detail": response.text}

    if response.is_error:
        raise HTTPException(
            status_code=response.status_code,
            detail=data,
        )

    return data


def _geojson_feature(
    latitude: float,
    longitude: float,
    properties: dict,
) -> dict:
    """Build one map-ready GeoJSON point feature."""

    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [longitude, latitude],
        },
        "properties": properties,
    }


@router.get("/map/weather/current", tags=["Map"])
async def get_current_weather_map_layer(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    """Return the current M1 weather observation as a GeoJSON layer."""

    weather = await _forward_get(
        MEMBER1_API_URL,
        "/weather/current",
        {"latitude": latitude, "longitude": longitude},
    )

    return {
        "type": "FeatureCollection",
        "features": [
            _geojson_feature(
                weather.get("latitude", latitude),
                weather.get("longitude", longitude),
                weather,
            )
        ],
    }


@router.get("/map/intelligence/current", tags=["Map"])
async def get_current_intelligence_map_layer(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    location_name: str | None = None,
):
    """Return current M3 risk, hazards, and alerts as a GeoJSON layer."""

    intelligence = await _forward_get(
        MEMBER3_API_URL,
        "/api/v1/intelligence/current",
        {
            "latitude": latitude,
            "longitude": longitude,
            "location_name": location_name,
        },
    )

    return {
        "type": "FeatureCollection",
        "features": [
            _geojson_feature(
                latitude,
                longitude,
                intelligence,
            )
        ],
    }


@router.get("/weather/current", tags=["Weather"])
async def get_current_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    return await _forward_get(
        MEMBER1_API_URL,
        "/weather/current",
        {"latitude": latitude, "longitude": longitude},
    )


@router.get("/weather/forecast", tags=["Weather"])
async def get_weather_forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    forecast_days: int = Query(7, ge=1, le=16),
):
    return await _forward_get(
        MEMBER1_API_URL,
        "/weather/forecast",
        {
            "latitude": latitude,
            "longitude": longitude,
            "forecast_days": forecast_days,
        },
    )


@router.get("/weather/historical", tags=["Weather"])
async def get_historical_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    start_date: str = Query(...),
    end_date: str = Query(...),
):
    return await _forward_get(
        MEMBER1_API_URL,
        "/weather/historical",
        {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


@router.get("/weather/imd", tags=["Weather"])
async def get_imd_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    return await _forward_get(
        MEMBER1_API_URL,
        "/weather/imd",
        {"latitude": latitude, "longitude": longitude},
    )


@router.get("/weather/satellite", tags=["Weather"])
async def get_satellite_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    return await _forward_get(
        MEMBER1_API_URL,
        "/weather/satellite",
        {"latitude": latitude, "longitude": longitude},
    )


@router.get("/intelligence/current", tags=["Intelligence"])
async def get_current_intelligence(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    location_name: str | None = None,
):
    return await _forward_get(
        MEMBER3_API_URL,
        "/api/v1/intelligence/current",
        {
            "latitude": latitude,
            "longitude": longitude,
            "location_name": location_name,
        },
    )


@router.get("/intelligence/forecast", tags=["Intelligence"])
async def get_forecast_intelligence(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    forecast_days: int = Query(7, ge=1, le=16),
    location_name: str | None = None,
):
    return await _forward_get(
        MEMBER3_API_URL,
        "/api/v1/intelligence/forecast",
        {
            "latitude": latitude,
            "longitude": longitude,
            "forecast_days": forecast_days,
            "location_name": location_name,
        },
    )


@router.get("/intelligence/historical", tags=["Intelligence"])
async def get_historical_intelligence(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    start_date: str = Query(...),
    end_date: str = Query(...),
    baselines: str = Query(...),
    location_name: str | None = None,
):
    return await _forward_get(
        MEMBER3_API_URL,
        "/api/v1/intelligence/historical",
        {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "baselines": baselines,
            "location_name": location_name,
        },
    )
