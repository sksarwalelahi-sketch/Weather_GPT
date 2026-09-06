from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class MQTTWeather(BaseModel):
    """
    Canonical weather observation received through MQTT.

    Values use the WeatherGPT canonical units:
    - temperature: °C
    - relative_humidity: %
    - precipitation: mm
    - wind_speed: km/h
    - wind_direction: degrees
    """

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    temperature: float = Field(ge=-100, le=70)
    relative_humidity: float = Field(ge=0, le=100)

    wind_speed: float = Field(ge=0)
    wind_direction: float = Field(ge=0, le=360)

    precipitation: float = Field(ge=0)

    timestamp: datetime

    source: str = "mqtt"

    model_config = {
        "extra": "allow"
    }

    def normalized_timestamp(self) -> datetime:
        timestamp = self.timestamp

        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)

        return timestamp