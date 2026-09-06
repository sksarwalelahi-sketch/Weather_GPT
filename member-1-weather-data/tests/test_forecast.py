from datetime import date

import pytest

from app.models.weather import OpenMeteoForecastResponse
from app.normalization.weather_normalizer import WeatherNormalizer
from app.services.weather_service import WeatherService


def sample_forecast_response():
    return OpenMeteoForecastResponse.model_validate(
        {
            "latitude": 20.281195,
            "longitude": 85.843376,
            "generationtime_ms": 0.2,
            "utc_offset_seconds": 0,
            "timezone": "GMT",
            "timezone_abbreviation": "GMT",
            "elevation": 44.0,
            "daily_units": {
                "time": "iso8601",
                "temperature_2m_max": "°C",
                "temperature_2m_min": "°C",
                "precipitation_sum": "mm",
                "rain_sum": "mm",
                "weather_code": "wmo code",
                "wind_speed_10m_max": "km/h",
            },
            "daily": {
                "time": [
                    "2026-08-29",
                    "2026-08-30",
                    "2026-08-31",
                ],
                "temperature_2m_max": [
                    32.5,
                    33.1,
                    31.8,
                ],
                "temperature_2m_min": [
                    25.4,
                    25.8,
                    25.2,
                ],
                "precipitation_sum": [
                    5.2,
                    2.1,
                    8.4,
                ],
                "rain_sum": [
                    5.2,
                    2.1,
                    8.4,
                ],
                "weather_code": [
                    61,
                    3,
                    63,
                ],
                "wind_speed_10m_max": [
                    18.2,
                    16.5,
                    20.1,
                ],
            },
        }
    )


def test_forecast_model():
    forecast = sample_forecast_response()

    assert len(forecast.daily.time) == 3
    assert forecast.daily.temperature_max[0] == 32.5
    assert forecast.daily.temperature_min[0] == 25.4


def test_forecast_normalization():
    source = sample_forecast_response()

    forecast = WeatherNormalizer.normalize_forecast(source)

    assert forecast.source == "open-meteo"
    assert forecast.latitude == 20.281195
    assert len(forecast.forecast) == 3

    first_day = forecast.forecast[0]

    assert first_day.date == date(2026, 8, 29)
    assert first_day.temperature_max == 32.5
    assert first_day.temperature_min == 25.4
    assert first_day.precipitation == 5.2
    assert first_day.weather_code == 61


class FakeOpenMeteoClient:
    async def get_forecast(
        self,
        latitude,
        longitude,
        forecast_days,
    ):
        return sample_forecast_response()

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_forecast_service():
    service = WeatherService(
        client=FakeOpenMeteoClient()
    )

    forecast = await service.get_forecast(
        latitude=20.2961,
        longitude=85.8245,
        forecast_days=3,
    )

    assert len(forecast.forecast) == 3
    assert forecast.forecast[0].temperature_max == 32.5


def test_forecast_days_validation():
    from app.openmeteo.client import OpenMeteoClient

    client = OpenMeteoClient()

    try:
        with pytest.raises(ValueError):
            import asyncio

            asyncio.run(
                client.get_forecast(
                    latitude=20.2961,
                    longitude=85.8245,
                    forecast_days=17,
                )
            )
    finally:
        import asyncio

        asyncio.run(client.close())