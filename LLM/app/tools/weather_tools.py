# app/tools/weather_tools.py

"""
WeatherGPT - Real Weather Tools

Uses the Member 1 data contract. Member 1 owns provider selection:
Open-Meteo supplies current weather, hourly/daily forecasts, and air quality.
"""

import os

import requests
from datetime import datetime, timedelta

from app.location.gis import get_coordinates

MEMBER1_API_URL = os.getenv(
    "MEMBER1_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


# =========================================================
# WEATHER API
# =========================================================

def get_weather_data(location: str):
    place = get_coordinates(location)
    return place, get_member1_weather(
        "/weather/forecast",
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "forecast_days": 7,
        },
    )


def get_member1_weather(
    endpoint: str,
    params: dict,
) -> dict:
    """Get canonical weather data from the Member 1 API."""

    response = requests.get(
        f"{MEMBER1_API_URL}{endpoint}",
        params=params,
        timeout=15,
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# WEATHER CODE
# =========================================================

def weather_description(code):

    codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }

    return codes.get(
        code,
        "Unknown weather condition"
    )


# =========================================================
# CURRENT WEATHER
# =========================================================

def get_current_weather(location: str) -> dict:

    place = get_coordinates(location)

    current = get_member1_weather(
        "/weather/current",
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
        },
    )

    weather_code = current.get("weather_code")

    return {
        "tool": "get_current_weather",
        "location": place["name"],
        "status": "live_data",
        "data": {
            "temperature_c": current.get(
                "temperature"
            ),
            "condition": weather_description(
                weather_code
            ),
            "humidity": current.get(
                "relative_humidity"
            ),
            "wind_speed_kmh": current.get(
                "wind_speed"
            ),
            "air_quality_index": current.get("air_quality_index"),
            "source": current.get("source", "open-meteo"),
        }
    }


# =========================================================
# FORECAST
# =========================================================

def get_forecast(
    location: str,
    time: str = "tomorrow"
) -> dict:

    place = get_coordinates(location)

    forecast_data = get_member1_weather(
        "/weather/forecast",
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "forecast_days": 7,
        },
    )

    forecast = forecast_data.get("forecast", [])

    dates = [item.get("date") for item in forecast]

    if not dates:
        raise ValueError(
            "Forecast data is unavailable."
        )

    # Find requested date
    target_date = datetime.now().date()

    if time.lower() in [
        "tomorrow",
        "next day"
    ]:
        target_date = target_date + timedelta(days=1)

    elif time.lower() in [
        "today",
        "now",
        "tonight",
    ]:
        target_date = target_date

    else:
        # Try YYYY-MM-DD
        try:
            target_date = datetime.strptime(
                time,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            target_date = target_date + timedelta(days=1)

    target_string = target_date.isoformat()

    if target_string not in dates:

        raise ValueError(
            f"Forecast unavailable for {target_string}"
        )

    index = dates.index(target_string)

    daily_weather = forecast[index]
    hourly = forecast_data.get("hourly") or {}
    hourly_times = hourly.get("time") or []
    hourly_probability = hourly.get("precipitation_probability") or []
    hourly_precipitation = hourly.get("precipitation") or []
    hourly_rain = hourly.get("rain") or []
    hourly_weather_codes = hourly.get("weather_code") or []
    hourly_temperature = hourly.get("temperature_2m") or []

    selected_hours = []
    for hour_index, timestamp in enumerate(hourly_times):
        try:
            parsed_time = datetime.fromisoformat(timestamp)
        except (TypeError, ValueError):
            continue
        if parsed_time.date() != target_date:
            continue
        if time.lower() == "tonight" and parsed_time.hour < 18:
            continue
        selected_hours.append(hour_index)

    if selected_hours:
        probability_values = [
            hourly_probability[i]
            for i in selected_hours
            if i < len(hourly_probability) and hourly_probability[i] is not None
        ]
        precipitation_values = [
            hourly_precipitation[i]
            for i in selected_hours
            if i < len(hourly_precipitation) and hourly_precipitation[i] is not None
        ]
        rain_values = [
            hourly_rain[i]
            for i in selected_hours
            if i < len(hourly_rain) and hourly_rain[i] is not None
        ]
        code_values = [
            hourly_weather_codes[i]
            for i in selected_hours
            if i < len(hourly_weather_codes)
        ]
        temperature_values = [
            hourly_temperature[i]
            for i in selected_hours
            if i < len(hourly_temperature) and hourly_temperature[i] is not None
        ]
        rain_probability = max(probability_values) if probability_values else None
        precipitation = sum(precipitation_values) if precipitation_values else None
        rainfall = sum(rain_values) if rain_values else precipitation
        weather_code = max(code_values) if code_values else daily_weather.get("weather_code")
        temperature_max = max(temperature_values) if temperature_values else daily_weather.get("temperature_max")
        temperature_min = min(temperature_values) if temperature_values else daily_weather.get("temperature_min")
    else:
        rain_probability = None
        precipitation = daily_weather.get("precipitation")
        rainfall = daily_weather.get("rain")
        weather_code = daily_weather.get("weather_code")
        temperature_max = daily_weather.get("temperature_max")
        temperature_min = daily_weather.get("temperature_min")

    return {
        "tool": "get_forecast",
        "location": place["name"],
        "time": time,
        "status": "live_data",
        "data": {
            "date": target_string,
            "temperature_max_c": temperature_max,
            "temperature_min_c": temperature_min,
            "condition": weather_description(
                weather_code
            ),
            "rain_probability": rain_probability,
            "precipitation_mm": precipitation,
            "rainfall_mm": rainfall,
        }
    }


# =========================================================
# ALERTS
# =========================================================

def get_alerts(location: str) -> dict:
    place = get_coordinates(location)
    intelligence = _get_current_intelligence(location)
    official_alerts: list[dict] = []
    try:
        response = requests.get(
            f"{MEMBER1_API_URL}/alerts/live",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "area": place.get("name") or location,
            },
            timeout=15,
        )
        response.raise_for_status()
        official_alerts = response.json().get("alerts", [])
    except requests.RequestException:
        # The local intelligence result remains useful when the alert store is
        # unavailable; it is explicitly labeled as non-official below.
        official_alerts = []

    if intelligence is None and not official_alerts:
        return _intelligence_unavailable("get_alerts", location)

    return {
        "tool": "get_alerts",
        "location": location,
        "status": "live_data",
        "data": {
            "official_alerts": official_alerts,
            "hazards": intelligence.get("hazards", []) if intelligence else [],
            "alerts": intelligence.get("alerts", []) if intelligence else [],
            "advisories": intelligence.get("advisories", []) if intelligence else [],
        }
    }


def get_flood_data(location: str) -> dict:
    """Fetch source-labelled flood data through Member 1."""
    place = get_coordinates(location)
    try:
        response = requests.get(
            f"{MEMBER1_API_URL}/weather/flood",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
            },
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        return {
            "tool": "get_flood_data",
            "location": location,
            "status": "live_data" if payload.get("status") == "live" else "provider_unavailable",
            "data": payload,
        }
    except requests.RequestException as exc:
        return {
            "tool": "get_flood_data",
            "location": location,
            "status": "service_unavailable",
            "data": {
                "message": f"Flood provider service is unavailable: {exc}",
            },
        }


# =========================================================
# CLIMATE
# =========================================================

def get_climate_analysis(
    location: str,
    start_date: str | None = None,
    end_date: str | None = None,
    baselines: dict[str, float] | None = None,
) -> dict:

    if not start_date or not end_date or not baselines:
        return {
            "tool": "get_climate_analysis",
            "location": location,
            "status": "input_required",
            "data": {
                "message": (
                    "Climate analysis requires a historical date range "
                    "and baseline values."
                )
            }
        }

    from app.intelligence.member3_client import get_climate_intelligence

    intelligence = get_climate_intelligence(
        location,
        start_date,
        end_date,
        baselines,
    )

    if intelligence is None:
        return _intelligence_unavailable(
            "get_climate_analysis",
            location,
        )

    return {
        "tool": "get_climate_analysis",
        "location": location,
        "status": "intelligence_data",
        "data": {
            "climate_analysis": intelligence.get(
                "climate_analysis",
                [],
            ),
        }
    }


# =========================================================
# AGRICULTURE
# =========================================================

def get_agriculture_advisory(location: str) -> dict:

    return _get_domain_advisories(
        location,
        "get_agriculture_advisory",
        "agriculture",
    )


# =========================================================
# AVIATION
# =========================================================

def get_aviation_advisory(location: str) -> dict:

    return _get_domain_advisories(
        location,
        "get_aviation_advisory",
        "aviation",
    )


# =========================================================
# MARINE
# =========================================================

def get_marine_advisory(location: str) -> dict:

    return _get_domain_advisories(
        location,
        "get_marine_advisory",
        "marine",
    )


def _get_current_intelligence(location: str) -> dict | None:
    """Return the existing Member 3 current-intelligence result."""

    from app.intelligence.member3_client import get_intelligence

    return get_intelligence(
        location,
        "get_current_weather",
    )


def _intelligence_unavailable(
    tool: str,
    location: str,
) -> dict:
    return {
        "tool": tool,
        "location": location,
        "status": "service_unavailable",
        "data": {
            "message": (
                "Weather intelligence service is unavailable."
            )
        }
    }


def _get_domain_advisories(
    location: str,
    tool: str,
    domain: str,
) -> dict:
    intelligence = _get_current_intelligence(location)

    if intelligence is None:
        return _intelligence_unavailable(tool, location)

    advisories = [
        advisory
        for advisory in intelligence.get("advisories", [])
        if advisory.get("domain") == domain.upper()
    ]

    return {
        "tool": tool,
        "location": location,
        "status": "intelligence_data",
        "data": {
            "advisories": advisories,
            "hazards": intelligence.get("hazards", []),
        }
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print("\n======================================")
    print("       WeatherGPT Real Weather")
    print("======================================")

    location = "Bhubaneswar"

    try:

        print("\nCurrent Weather:")
        print(
            get_current_weather(location)
        )

        print("\nTomorrow Forecast:")
        print(
            get_forecast(
                location,
                "tomorrow"
            )
        )

        print("\n===== TEST COMPLETE =====")

    except Exception as error:

        print("\nERROR:")
        print(error)
