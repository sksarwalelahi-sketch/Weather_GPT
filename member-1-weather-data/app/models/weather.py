from datetime import date, datetime

from pydantic import BaseModel, Field


class CurrentWeather(BaseModel):
    time: datetime

    temperature: float = Field(alias="temperature_2m")
    relative_humidity: float = Field(alias="relative_humidity_2m")
    apparent_temperature: float = Field(alias="apparent_temperature")

    precipitation: float
    rain: float
    weather_code: int
    cloud_cover: float
    surface_pressure: float

    wind_speed: float = Field(alias="wind_speed_10m")
    wind_direction: float = Field(alias="wind_direction_10m")
    wind_gusts: float = Field(alias="wind_gusts_10m")

    model_config = {
        "populate_by_name": True
    }


class OpenMeteoResponse(BaseModel):
    latitude: float
    longitude: float
    generationtime_ms: float
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
    elevation: float

    current_units: dict[str, str]
    current: CurrentWeather


class DailyForecast(BaseModel):
    time: list[date]

    temperature_max: list[float] = Field(
        alias="temperature_2m_max"
    )
    temperature_min: list[float] = Field(
        alias="temperature_2m_min"
    )
    precipitation_sum: list[float]
    rain_sum: list[float]
    weather_code: list[int]
    wind_speed_max: list[float] = Field(
        alias="wind_speed_10m_max"
    )

    model_config = {
        "populate_by_name": True
    }


class OpenMeteoForecastResponse(BaseModel):
    latitude: float
    longitude: float
    generationtime_ms: float
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
    elevation: float

    daily_units: dict[str, str]
    daily: DailyForecast


class DailyHistoricalWeather(BaseModel):
    time: list[date]

    temperature_max: list[float] = Field(
        alias="temperature_2m_max"
    )
    temperature_min: list[float] = Field(
        alias="temperature_2m_min"
    )
    precipitation_sum: list[float]
    rain_sum: list[float]
    weather_code: list[int]
    wind_speed_max: list[float] = Field(
        alias="wind_speed_10m_max"
    )

    model_config = {
        "populate_by_name": True
    }


class OpenMeteoHistoricalResponse(BaseModel):
    latitude: float
    longitude: float
    generationtime_ms: float
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
    elevation: float

    daily_units: dict[str, str]
    daily: DailyHistoricalWeather
