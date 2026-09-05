"""
WeatherGPT - Member 3
Member 1 -> Member 3 Integration Adapter

Converts the actual Member 1 Weather Data & NWP API responses
into the standardized input structures consumed by Member 3.

Important:
- This adapter does not modify Member 1 data.
- Missing fields remain None.
- M1 `rain` is mapped to M3 `rainfall`.
- M1 `precipitation` is intentionally NOT mapped to
  `precipitation_probability`.
- Daily forecast temperature uses `temperature_max` for
  weather-risk screening.
- Daily forecast wind speed uses `wind_speed_max`.
"""

from __future__ import annotations

from datetime import datetime, time
from typing import Any

from schemas.weather import WeatherInput


# ---------------------------------------------------------------------
# Current Weather
# ---------------------------------------------------------------------


def current_to_weather_input(
    payload: dict[str, Any],
    location_name: str | None = None,
) -> WeatherInput:
    """
    Convert the actual Member 1 /weather/current response
    into a Member 3 WeatherInput.

    Expected Member 1 fields:
        latitude
        longitude
        observed_at
        temperature
        apparent_temperature
        relative_humidity
        surface_pressure
        rain
        wind_speed
        wind_direction
        wind_gusts
        source

    Fields intentionally not populated because M1 does not provide
    them:
        precipitation_probability
        visibility
        forecast_horizon_hours
    """

    return WeatherInput(
        location_name=location_name,
        latitude=payload["latitude"],
        longitude=payload["longitude"],
        timestamp=datetime.fromisoformat(payload["observed_at"]),
        temperature=payload.get("temperature"),
        feels_like=payload.get("apparent_temperature"),
        humidity=payload.get("relative_humidity"),
        pressure=payload.get("surface_pressure"),
        rainfall=payload.get("rain"),
        precipitation_probability=None,
        wind_speed=payload.get("wind_speed"),
        wind_direction=payload.get("wind_direction"),
        wind_gust=payload.get("wind_gusts"),
        visibility=None,
        source=payload.get("source"),
        forecast_horizon_hours=None,
    )


# ---------------------------------------------------------------------
# Daily Forecast
# ---------------------------------------------------------------------


def forecast_to_weather_inputs(
    payload: dict[str, Any],
    location_name: str | None = None,
) -> list[WeatherInput]:
    """
    Convert the actual Member 1 /weather/forecast response
    into a list of Member 3 WeatherInput objects.

    M1 provides daily forecast data rather than timestamp-level
    observations.

    Modeling decisions:
        temperature_max -> temperature
        rain            -> rainfall
        wind_speed_max  -> wind_speed

    Missing M1 fields remain None.

    The daily date is represented at 00:00:00 because the source
    provides a date rather than an exact forecast timestamp.
    """

    latitude = payload["latitude"]
    longitude = payload["longitude"]
    source = payload.get("source")

    weather_inputs: list[WeatherInput] = []

    for forecast in payload.get("forecast", []):
        forecast_date = datetime.fromisoformat(
            forecast["date"]
        ).date()

        timestamp = datetime.combine(
            forecast_date,
            time.min,
        )

        weather_inputs.append(
            WeatherInput(
                location_name=location_name,
                latitude=latitude,
                longitude=longitude,
                timestamp=timestamp,
                temperature=forecast.get("temperature_max"),
                feels_like=None,
                humidity=None,
                pressure=None,
                rainfall=forecast.get("rain"),
                precipitation_probability=None,
                wind_speed=forecast.get("wind_speed_max"),
                wind_direction=None,
                wind_gust=None,
                visibility=None,
                source=source,
                forecast_horizon_hours=None,
            )
        )

    return weather_inputs


# ---------------------------------------------------------------------
# Historical Weather
# ---------------------------------------------------------------------


def historical_to_climate_values(
    payload: dict[str, Any],
    baselines: dict[str, float],
    location_name: str | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Convert the actual Member 1 /weather/historical response
    into the historical_values structure expected by the
    Member 3 decision engine.

    M1 daily fields are mapped as follows:

        temperature_max -> temperature
        rain            -> rainfall
        wind_speed_max  -> wind_speed

    Humidity is not included because M1's current historical
    response does not provide historical humidity.

    `baselines` must be supplied by the caller. The adapter does
    not invent climate baselines.

    Example:

        baselines = {
            "temperature": 30.0,
            "rainfall": 5.0,
            "wind_speed": 15.0,
        }

    Returns:

        {
            "temperature": {
                "values": [...],
                "baseline": 30.0,
                "period": "2026-08-18 to 2026-08-20",
            },
            "rainfall": {
                "values": [...],
                "baseline": 5.0,
                "period": "2026-08-18 to 2026-08-20",
            },
            "wind_speed": {
                "values": [...],
                "baseline": 15.0,
                "period": "2026-08-18 to 2026-08-20",
            },
        }
    """

    historical = payload.get("historical", [])

    start_date = payload.get("start_date")
    end_date = payload.get("end_date")

    if start_date and end_date:
        period = f"{start_date} to {end_date}"
    else:
        period = "Historical period"

    climate_values: dict[str, dict[str, Any]] = {}

    metric_extractors = {
        "temperature": "temperature_max",
        "rainfall": "rain",
        "wind_speed": "wind_speed_max",
    }

    for metric_name, field_name in metric_extractors.items():
        if metric_name not in baselines:
            continue

        values = [
            record[field_name]
            for record in historical
            if record.get(field_name) is not None
        ]

        if not values:
            continue

        climate_values[metric_name] = {
            "values": values,
            "baseline": baselines[metric_name],
            "period": period,
        }

    return climate_values