from datetime import datetime, timezone

from pydantic import BaseModel, Field


class LocationData(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class TemperatureData(BaseModel):
    temperature: float = Field(ge=-100, le=70)


class HumidityData(BaseModel):
    relative_humidity: float = Field(ge=0, le=100)


class PrecipitationData(BaseModel):
    precipitation: float = Field(ge=0)


class WindData(BaseModel):
    wind_speed: float = Field(ge=0)
    wind_direction: float = Field(ge=0, le=360)


class PressureData(BaseModel):
    surface_pressure: float = Field(gt=0)


class TimestampData(BaseModel):
    timestamp: datetime

    def validate_timestamp(self) -> datetime:
        timestamp = self.timestamp

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)

        if timestamp > now:
            difference = (timestamp - now).total_seconds()

            if difference > 300:
                raise ValueError(
                    "Timestamp cannot be more than 5 minutes in the future"
                )

        return timestamp