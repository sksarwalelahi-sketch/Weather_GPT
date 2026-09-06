from datetime import date, datetime

from pydantic import BaseModel

from app.models.weather import (
    OpenMeteoForecastResponse,
    OpenMeteoHistoricalResponse,
    OpenMeteoResponse,
)


class CanonicalWeather(BaseModel):
    latitude: float
    longitude: float

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

    source: str


class CanonicalDailyForecast(BaseModel):
    date: date
    temperature_max: float
    temperature_min: float
    precipitation: float
    rain: float
    weather_code: int
    wind_speed_max: float


class CanonicalForecast(BaseModel):
    latitude: float
    longitude: float
    timezone: str
    source: str
    forecast: list[CanonicalDailyForecast]


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

        return CanonicalWeather(
            latitude=weather.latitude,
            longitude=weather.longitude,
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
                rain=rain,
                weather_code=weather_code,
                wind_speed_max=wind_speed_max,
            )
            for (
                forecast_date,
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

        return CanonicalForecast(
            latitude=weather.latitude,
            longitude=weather.longitude,
            timezone=weather.timezone,
            source=cls.SOURCE,
            forecast=forecast,
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