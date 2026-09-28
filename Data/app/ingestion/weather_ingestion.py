from app.normalization.weather_normalizer import (
    WeatherNormalizer,
)
from app.openmeteo.client import OpenMeteoClient
from app.repositories.weather_repository import WeatherRepository
from app.validation.weather_validator import (
    HumidityData,
    LocationData,
    PrecipitationData,
    PressureData,
    TemperatureData,
    TimestampData,
    WindData,
)


class WeatherIngestion:
    """
    Weather data ingestion pipeline.

    External Provider
          ↓
    OpenMeteoClient
          ↓
    Validation
          ↓
    Normalization
          ↓
    Repository
    """

    SOURCE = "open-meteo"

    def __init__(
        self,
        client: OpenMeteoClient | None = None,
        repository: WeatherRepository | None = None,
    ):
        self.client = client or OpenMeteoClient()
        self.repository = repository

    @staticmethod
    def _validate_current(weather) -> None:
        LocationData(
            latitude=weather.latitude,
            longitude=weather.longitude,
        )

        current = weather.current

        TemperatureData(
            temperature=current.temperature,
        )

        HumidityData(
            relative_humidity=current.relative_humidity,
        )

        PrecipitationData(
            precipitation=current.precipitation,
        )

        WindData(
            wind_speed=current.wind_speed,
            wind_direction=current.wind_direction,
        )

        PressureData(
            surface_pressure=current.surface_pressure,
        )

        TimestampData(
            timestamp=current.time,
        ).validate_timestamp()

    @staticmethod
    def _validate_forecast(forecast) -> None:
        LocationData(
            latitude=forecast.latitude,
            longitude=forecast.longitude,
        )

        daily = forecast.daily

        if not (
            len(daily.time)
            == len(daily.temperature_max)
            == len(daily.temperature_min)
            == len(daily.precipitation_sum)
            == len(daily.rain_sum)
            == len(daily.weather_code)
            == len(daily.wind_speed_max)
        ):
            raise ValueError(
                "Forecast arrays must have equal lengths"
            )

        for temperature in daily.temperature_max:
            TemperatureData(
                temperature=temperature,
            )

        for temperature in daily.temperature_min:
            TemperatureData(
                temperature=temperature,
            )

        for precipitation in daily.precipitation_sum:
            PrecipitationData(
                precipitation=precipitation,
            )

        for rain in daily.rain_sum:
            PrecipitationData(
                precipitation=rain,
            )

        for wind_speed in daily.wind_speed_max:
            WindData(
                wind_speed=wind_speed,
                wind_direction=0,
            )

    @staticmethod
    def _validate_historical(historical) -> None:
        LocationData(
            latitude=historical.latitude,
            longitude=historical.longitude,
        )

        daily = historical.daily

        if not (
            len(daily.time)
            == len(daily.temperature_max)
            == len(daily.temperature_min)
            == len(daily.precipitation_sum)
            == len(daily.rain_sum)
            == len(daily.weather_code)
            == len(daily.wind_speed_max)
        ):
            raise ValueError(
                "Historical arrays must have equal lengths"
            )

        for temperature in daily.temperature_max:
            TemperatureData(
                temperature=temperature,
            )

        for temperature in daily.temperature_min:
            TemperatureData(
                temperature=temperature,
            )

        for precipitation in daily.precipitation_sum:
            PrecipitationData(
                precipitation=precipitation,
            )

        for rain in daily.rain_sum:
            PrecipitationData(
                precipitation=rain,
            )

        for wind_speed in daily.wind_speed_max:
            WindData(
                wind_speed=wind_speed,
                wind_direction=0,
            )

    async def ingest_current(
        self,
        latitude: float,
        longitude: float,
    ):
        weather = await self.client.get_weather(
            latitude=latitude,
            longitude=longitude,
        )

        self._validate_current(weather)

        canonical = WeatherNormalizer.normalize(
            weather
        )

        if self.repository is not None:
            await self.repository.save_current(
                canonical
            )

        return canonical

    async def ingest_forecast(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 7,
    ):
        forecast = await self.client.get_forecast(
            latitude=latitude,
            longitude=longitude,
            forecast_days=forecast_days,
        )

        self._validate_forecast(forecast)

        canonical = WeatherNormalizer.normalize_forecast(
            forecast
        )

        if self.repository is not None:
            await self.repository.save_forecast(
                canonical
            )

        return canonical

    async def ingest_historical(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
    ):
        historical = await self.client.get_historical(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
        )

        self._validate_historical(historical)

        canonical = WeatherNormalizer.normalize_historical(
            historical
        )

        if self.repository is not None:
            await self.repository.save_historical(
                canonical
            )

        return canonical

    async def close(self) -> None:
        await self.client.close()