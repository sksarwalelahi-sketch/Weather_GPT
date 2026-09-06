from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class IMDWeather(BaseModel):
    """
    Normalized IMD weather observation.

    Provider-neutral model for official IMD weather feeds.
    """

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    timestamp: datetime

    temperature: float | None = None

    relative_humidity: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    precipitation: float | None = Field(
        default=None,
        ge=0,
    )

    wind_speed: float | None = Field(
        default=None,
        ge=0,
    )

    wind_direction: float | None = Field(
        default=None,
        ge=0,
        le=360,
    )

    pressure: float | None = Field(
        default=None,
        ge=0,
    )

    source: str = "imd"

    station_id: str | None = None

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