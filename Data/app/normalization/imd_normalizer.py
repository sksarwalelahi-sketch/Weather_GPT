from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.imd_weather import IMDWeather


class IMDWeatherNormalizer:
    """
    Converts official IMD/provider payloads into the
    common WeatherGPT weather structure.
    """

    SOURCE = "imd"

    FIELD_ALIASES = {
        "lat": "latitude",
        "lon": "longitude",
        "Latitude": "latitude",
        "Longitude": "longitude",
        "time": "timestamp",
        "observed_at": "timestamp",
        "Date": "timestamp",
        "temp": "temperature",
        "temperature_2m": "temperature",
        "Temperature": "temperature",
        "Today_Max_temp": "temperature",
        "humidity": "relative_humidity",
        "rh": "relative_humidity",
        "Humidity": "relative_humidity",
        "Relative_Humidity_at_0830": "relative_humidity",
        "rain": "precipitation",
        "rainfall": "precipitation",
        "Past_24_hrs_Rainfall": "precipitation",
        "wind": "wind_speed",
        "wind_speed_10m": "wind_speed",
        "Wind Speed KMPH": "wind_speed",
        "wind_direction_10m": "wind_direction",
        "Wind Direction": "wind_direction",
        "pressure": "pressure",
        "surface_pressure": "pressure",
        "Mean Sea Level Pressure": "pressure",
        "station": "station_id",
        "Station_Code": "station_id",
        "Station Id": "station_id",
    }

    @classmethod
    def normalize(
        cls,
        payload: dict[str, Any] | list[dict[str, Any]],
    ) -> IMDWeather:

        if isinstance(payload, list):
            if not payload or not isinstance(payload[0], dict):
                raise TypeError(
                    "IMD payload list must contain an observation dictionary"
                )
            payload = payload[0]

        if not isinstance(payload, dict):
            raise TypeError(
                "IMD payload must be a dictionary"
            )

        data = dict(payload)

        # Support nested provider payloads.
        if isinstance(data.get("data"), dict):
            nested = dict(data["data"])

            for key, value in nested.items():
                data.setdefault(key, value)

        # Apply aliases.
        for source_field, target_field in (
            cls.FIELD_ALIASES.items()
        ):
            if (
                target_field not in data
                and source_field in data
            ):
                data[target_field] = data[
                    source_field
                ]

        if isinstance(data.get("timestamp"), str):
            for date_format in ("%d-%m-%Y", "%d/%m/%Y"):
                try:
                    data["timestamp"] = datetime.strptime(
                        data["timestamp"],
                        date_format,
                    ).replace(tzinfo=timezone.utc)
                    break
                except ValueError:
                    continue

        data.setdefault(
            "source",
            cls.SOURCE,
        )

        if "timestamp" not in data:
            data["timestamp"] = datetime.now(
                timezone.utc
            )

        return IMDWeather.model_validate(data)