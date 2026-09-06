from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class SatelliteWeather(BaseModel):
    """
    Normalized satellite-derived weather observation.

    Provider-neutral structure for MOSDAC/INSAT
    satellite weather products.
    """

    latitude: float = Field(
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ge=-180,
        le=180,
    )

    timestamp: datetime

    cloud_cover: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    brightness_temperature: float | None = None

    rainfall_estimate: float | None = Field(
        default=None,
        ge=0,
    )

    solar_radiation: float | None = Field(
        default=None,
        ge=0,
    )

    source: str = "mosdac"

    product: str = "satellite"

    model_config = {
        "extra": "allow",
    }

    def normalized_timestamp(self) -> datetime:
        timestamp = self.timestamp

        if timestamp.tzinfo is None:
            return timestamp.replace(
                tzinfo=timezone.utc
            )

        return timestamp.astimezone(
            timezone.utc
        )