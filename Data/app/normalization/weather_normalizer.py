from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.weather import (
    OpenMeteoForecastResponse,
    OpenMeteoHistoricalResponse,
    OpenMeteoResponse,
)


class CanonicalWeather(BaseModel):
    latitude: float
    longitude: float
    timezone: str
    timezone_abbreviation: str

    observed_at: datetime

    temperature: float
    apparent_temperature: float
    relative_humidity: float

    precipitation: float
    rain: float

    weather_code: int
    cloud_cover: float
    surface_pressure: float

    wind_speed: float
    wind_direction: float
    wind_gusts: float
    visibility: float | None = None
    uv_index: float | None = None
    dew_point: float | None = None
    sunrise: datetime | None = None
    sunset: datetime | None = None
    air_quality_index: float | None = None

    source: str
    retrieved_at: datetime | None = None
    provenance: dict[str, object] = Field(default_factory=dict)


class CanonicalDailyForecast(BaseModel):
    date: date
    temperature_max: float
    temperature_min: float
    precipitation: float
    precipitation_probability: float | None = None
    rain: float
    weather_code: int
    wind_speed_max: float
    humidity: float | None = None


class CanonicalForecast(BaseModel):
    latitude: float
    longitude: float
    timezone: str
    source: str
    forecast: list[CanonicalDailyForecast]
    hourly: dict[str, list] | None = None
    sunrise: list[str] = Field(default_factory=list)
    sunset: list[str] = Field(default_factory=list)
    retrieved_at: datetime | None = None
    provenance: dict[str, object] = Field(default_factory=dict)


class CanonicalDailyHistorical(BaseModel):
    date: date
    temperature_max: float
    temperature_min: float
    precipitation: float
    rain: float
    weather_code: int
    wind_speed_max: float


class CanonicalHistorical(BaseModel):
    latitude: float
    longitude: float
    timezone: str
    source: str
    start_date: date
    end_date: date
    historical: list[CanonicalDailyHistorical]


class WeatherNormalizer:
    SOURCE = "open-meteo"

    @classmethod
    def normalize(
        cls,
        weather: OpenMeteoResponse,
    ) -> CanonicalWeather:
        current = weather.current
        daily = getattr(weather, "daily", None)

        return CanonicalWeather(
            latitude=weather.latitude,
            longitude=weather.longitude,
            timezone=getattr(weather, "timezone", "UTC"),
            timezone_abbreviation=getattr(weather, "timezone_abbreviation", "UTC"),
            observed_at=current.time,
            temperature=current.temperature,
            apparent_temperature=current.apparent_temperature,
            relative_humidity=current.relative_humidity,
            precipitation=current.precipitation,
            rain=current.rain,
            weather_code=current.weather_code,
            cloud_cover=current.cloud_cover,
            surface_pressure=current.surface_pressure,
            wind_speed=current.wind_speed,
            wind_direction=current.wind_direction,
            wind_gusts=current.wind_gusts,
            visibility=getattr(current, "visibility", None),
            uv_index=getattr(current, "uv_index", None),
            dew_point=getattr(current, "dew_point", None),
            sunrise=(
                datetime.fromisoformat(daily["sunrise"][0])
                if daily and daily.get("sunrise")
                else None
            ),
            sunset=(
                datetime.fromisoformat(daily["sunset"][0])
                if daily and daily.get("sunset")
                else None
            ),
            source=cls.SOURCE,
        )

    @classmethod
    def normalize_forecast(
        cls,
        weather: OpenMeteoForecastResponse,
    ) -> CanonicalForecast:
        daily = weather.daily

        forecast = [
            CanonicalDailyForecast(
                date=forecast_date,
                temperature_max=temperature_max,
                temperature_min=temperature_min,
                precipitation=precipitation,
                precipitation_probability=(
                    daily.precipitation_probability_max[index]
                    if index < len(daily.precipitation_probability_max)
                    else None
                ),
                rain=rain,
                weather_code=weather_code,
                wind_speed_max=wind_speed_max,
                humidity=(
                    daily.relative_humidity_mean[index]
                    if index < len(daily.relative_humidity_mean)
                    else None
                ),
            )
            for index, (
                forecast_date,
                temperature_max,
                temperature_min,
                precipitation,
                rain,
                weather_code,
                wind_speed_max,
            ) in enumerate(zip(
                daily.time,
                daily.temperature_max,
                daily.temperature_min,
                daily.precipitation_sum,
                daily.rain_sum,
                daily.weather_code,
                daily.wind_speed_max,
            ))
        ]

        return CanonicalForecast(
            latitude=weather.latitude,
            longitude=weather.longitude,
            timezone=weather.timezone,
            source=cls.SOURCE,
            forecast=forecast,
            hourly=weather.hourly,
            sunrise=daily.sunrise,
            sunset=daily.sunset,
        )

    @classmethod
    def normalize_historical(
        cls,
        weather: OpenMeteoHistoricalResponse,
    ) -> CanonicalHistorical:
        daily = weather.daily

        if not daily.time:
            return CanonicalHistorical(
                latitude=weather.latitude,
                longitude=weather.longitude,
                timezone=weather.timezone,
                source=cls.SOURCE,
                start_date=date.min,
                end_date=date.min,
                historical=[],
            )

        historical = [
            CanonicalDailyHistorical(
                date=historical_date,
                temperature_max=temperature_max,
                temperature_min=temperature_min,
                precipitation=precipitation,
                rain=rain,
                weather_code=weather_code,
                wind_speed_max=wind_speed_max,
            )
            for (
                historical_date,
                temperature_max,
                temperature_min,
                precipitation,
                rain,
                weather_code,
                wind_speed_max,
            ) in zip(
                daily.time,
                daily.temperature_max,
                daily.temperature_min,
                daily.precipitation_sum,
                daily.rain_sum,
                daily.weather_code,
                daily.wind_speed_max,
            )
        ]

        return CanonicalHistorical(
            latitude=weather.latitude,
            longitude=weather.longitude,
            timezone=weather.timezone,
            source=cls.SOURCE,
            start_date=daily.time[0],
            end_date=daily.time[-1],
            historical=historical,
        )