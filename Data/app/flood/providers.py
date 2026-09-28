from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


PROVIDERS = {
    "noaa-nwm": {
        "name": "NOAA National Water Model",
        "url": settings.NOAA_FLOOD_API_URL,
    },
    "ecmwf-efas": {
        "name": "ECMWF EFAS",
        "url": settings.ECMWF_FLOOD_API_URL,
    },
    "dwd": {
        "name": "DWD Open Data",
        "url": settings.DWD_FLOOD_API_URL,
    },
}


async def get_flood_data(latitude: float, longitude: float) -> dict[str, Any]:
    """Fetch configured flood feeds without inventing unavailable values."""
    results: list[dict[str, Any]] = []
    async with httpx.AsyncClient(
        timeout=settings.FLOOD_PROVIDER_TIMEOUT_SECONDS
    ) as client:
        for provider_id, provider in PROVIDERS.items():
            url = provider["url"]
            if not url:
                results.append({
                    "provider": provider_id,
                    "name": provider["name"],
                    "status": "not_configured",
                    "message": "Configure the provider endpoint in Data/.env.",
                })
                continue
            try:
                response = await client.get(
                    url,
                    params={"latitude": latitude, "longitude": longitude},
                )
                response.raise_for_status()
                results.append({
                    "provider": provider_id,
                    "name": provider["name"],
                    "status": "live",
                    "data": response.json(),
                })
            except (httpx.HTTPError, ValueError) as exc:
                results.append({
                    "provider": provider_id,
                    "name": provider["name"],
                    "status": "unavailable",
                    "message": str(exc),
                })
    return {
        "latitude": latitude,
        "longitude": longitude,
        "sources": results,
        "status": "live" if any(item["status"] == "live" for item in results) else "unavailable",
        "provenance": {
            "providers": [item["provider"] for item in results],
            "role": "external flood observations and forecasts",
            "limitation": "Provider payloads are not blended until source-specific schemas are configured.",
        },
    }
