"""Client for the Member 3 weather-intelligence API."""

import json
import os

import requests

from app.tools.weather_tools import get_coordinates


MEMBER3_API_URL = os.getenv(
    "MEMBER3_API_URL",
    "http://127.0.0.1:8001",
).rstrip("/")


def get_intelligence(
    location: str,
    selected_tool: str,
) -> dict | None:
    """Return Member 3 intelligence for a location when the service is online."""

    place = get_coordinates(location)

    endpoint = "/api/v1/intelligence/current"
    params = {
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "location_name": place["name"],
    }

    if selected_tool == "get_forecast":
        endpoint = "/api/v1/intelligence/forecast"
        params["forecast_days"] = 7

    try:
        response = requests.get(
            f"{MEMBER3_API_URL}{endpoint}",
            params=params,
            timeout=5,
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException:
        return None


def get_climate_intelligence(
    location: str,
    start_date: str,
    end_date: str,
    baselines: dict[str, float],
) -> dict | None:
    """Return Member 3 historical climate intelligence for a location."""

    place = get_coordinates(location)

    try:
        response = requests.get(
            f"{MEMBER3_API_URL}/api/v1/intelligence/historical",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "start_date": start_date,
                "end_date": end_date,
                "baselines": json.dumps(baselines),
                "location_name": place["name"],
            },
            timeout=15,
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException:
        return None
