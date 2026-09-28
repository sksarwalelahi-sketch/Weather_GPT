import httpx
from app.core.config import settings

from app.models.weather import (
    OpenMeteoForecastResponse,
    OpenMeteoHistoricalResponse,
    OpenMeteoResponse,
)


class OpenMeteoClient:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                45.0,
                connect=15.0,
            ),
        )

    async def get_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> OpenMeteoResponse:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "models": settings.OPEN_METEO_NWP_MODELS,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "precipitation",
                "rain",
                "weather_code",
                "cloud_cover",
                "surface_pressure",
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m",
                "visibility",
                "uv_index",
                "dew_point_2m",
            ],
            "daily": ["sunrise", "sunset"],
            "timezone": "auto",
        }

        response = await self.client.get(
            self.BASE_URL,
            params=params,
        )

        response.raise_for_status()

        return OpenMeteoResponse.model_validate(
            response.json()
        )

    async def get_air_quality(
        self,
        latitude: float,
        longitude: float,
    ) -> dict:
        response = await self.client.get(
            "https://air-quality-api.open-meteo.com/v1/air-quality",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": ["us_aqi"],
                "timezone": "auto",
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 7,
    ) -> OpenMeteoForecastResponse:
        if not 1 <= forecast_days <= 16:
            raise ValueError(
                "forecast_days must be between 1 and 16"
            )

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": [
                "sunrise",
                "sunset",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "precipitation_probability_max",
                "rain_sum",
                "weather_code",
                "wind_speed_10m_max",
                "relative_humidity_2m_mean",
            ],
            "hourly": [
                "temperature_2m",
                "precipitation_probability",
                "precipitation",
                "rain",
                "weather_code",
                "wind_speed_10m",
            ],
            "forecast_days": forecast_days,
            "timezone": "auto",
        }

        response = await self.client.get(
            self.BASE_URL,
            params=params,
        )

        response.raise_for_status()

        return OpenMeteoForecastResponse.model_validate(
            response.json()
        )

    async def get_historical(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
    ) -> OpenMeteoHistoricalResponse:
        if start_date > end_date:
            raise ValueError(
                "start_date must be before or equal to end_date"
            )

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "rain_sum",
                "weather_code",
                "wind_speed_10m_max",
            ],
            "timezone": "UTC",
        }

        response = await self.client.get(
            self.HISTORICAL_URL,
            params=params,
        )

        response.raise_for_status()

        return OpenMeteoHistoricalResponse.model_validate(
            response.json()
        )

    async def close(self):
        await self.client.aclose()