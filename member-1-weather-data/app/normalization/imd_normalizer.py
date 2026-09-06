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
        "time": "timestamp",
        "observed_at": "timestamp",
        "temp": "temperature",
        "temperature_2m": "temperature",
        "humidity": "relative_humidity",
        "rh": "relative_humidity",
        "rain": "precipitation",
        "rainfall": "precipitation",
        "wind": "wind_speed",
        "wind_speed_10m": "wind_speed",
        "wind_direction_10m": "wind_direction",
        "pressure": "pressure",
        "surface_pressure": "pressure",
        "station": "station_id",
    }

    @classmethod
    def normalize(
        cls,
        payload: dict[str, Any],
    ) -> IMDWeather:

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

        data.setdefault(
            "source",
            cls.SOURCE,
        )

        if "timestamp" not in data:
            data["timestamp"] = datetime.now(
                timezone.utc
            )

        return IMDWeather.model_validate(data)