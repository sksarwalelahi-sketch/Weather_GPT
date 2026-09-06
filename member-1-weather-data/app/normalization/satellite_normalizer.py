from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.satellite_weather import (
    SatelliteWeather,
)


class SatelliteWeatherNormalizer:
    """
    Converts provider-specific satellite payloads
    into the common WeatherGPT satellite structure.
    """

    SOURCE = "mosdac"

    FIELD_ALIASES = {
        "lat": "latitude",
        "lon": "longitude",
        "time": "timestamp",
        "observed_at": "timestamp",
        "cloud": "cloud_cover",
        "cloud_fraction": "cloud_cover",
        "brightness_temp": "brightness_temperature",
        "bt": "brightness_temperature",
        "rainfall": "rainfall_estimate",
        "rain_rate": "rainfall_estimate",
        "solar": "solar_radiation",
        "radiation": "solar_radiation",
    }

    @classmethod
    def normalize(
        cls,
        payload: dict[str, Any],
    ) -> SatelliteWeather:

        if not isinstance(payload, dict):
            raise TypeError(
                "Satellite payload must be a dictionary"
            )

        data = dict(payload)

        # Support nested satellite payloads.
        if isinstance(data.get("data"), dict):
            nested = dict(data["data"])

            for key, value in nested.items():
                data.setdefault(key, value)

        # Apply common provider aliases.
        for (
            source_field,
            target_field,
        ) in cls.FIELD_ALIASES.items():

            if (
                target_field not in data
                and source_field in data
            ):
                data[target_field] = data[
                    source_field
                ]

        data.setdefault(
            "source",
            cls.SOURCE,
        )

        data.setdefault(
            "product",
            "satellite",
        )

        if "timestamp" not in data:
            data["timestamp"] = datetime.now(
                timezone.utc
            )

        return SatelliteWeather.model_validate(
            data
        )