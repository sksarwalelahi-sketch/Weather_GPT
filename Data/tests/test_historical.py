from datetime import date
import asyncio

import pytest

from app.models.weather import OpenMeteoHistoricalResponse
from app.normalization.weather_normalizer import WeatherNormalizer
from app.services.weather_service import WeatherService


def sample_historical_response():
    return OpenMeteoHistoricalResponse.model_validate(
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
                    "2026-08-25",
                    "2026-08-26",
                    "2026-08-27",
                ],
                "temperature_2m_max": [
                    31.2,
                    30.8,
                    32.1,
                ],
                "temperature_2m_min": [
                    25.1,
                    24.8,
                    25.4,
                ],
                "precipitation_sum": [
                    4.5,
                    12.2,
                    0.8,
                ],
                "rain_sum": [
                    4.5,
                    12.2,
                    0.8,
                ],
                "weather_code": [
                    61,
                    63,
                    3,
                ],
                "wind_speed_10m_max": [
                    17.2,
                    21.5,
                    15.8,
                ],
            },
        }
    )


def test_historical_model():
    historical = sample_historical_response()

    assert len(historical.daily.time) == 3
    assert historical.daily.temperature_max[0] == 31.2
    assert historical.daily.temperature_min[0] == 25.1


def test_historical_normalization():
    source = sample_historical_response()

    historical = WeatherNormalizer.normalize_historical(
        source
    )

    assert historical.source == "open-meteo"
    assert historical.latitude == 20.281195
    assert historical.longitude == 85.843376

    assert len(historical.historical) == 3

    assert historical.start_date == date(2026, 8, 25)
    assert historical.end_date == date(2026, 8, 27)

    first_day = historical.historical[0]

    assert first_day.date == date(2026, 8, 25)
    assert first_day.temperature_max == 31.2
    assert first_day.temperature_min == 25.1
    assert first_day.precipitation == 4.5
    assert first_day.weather_code == 61


class FakeHistoricalClient:
    async def get_historical(
        self,
        latitude,
        longitude,
        start_date,
        end_date,
    ):
        if start_date > end_date:
            raise ValueError(
                "start_date must be before or equal to end_date"
            )

        return sample_historical_response()

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_historical_service():
    service = WeatherService(
        client=FakeHistoricalClient()
    )

    historical = await service.get_historical(
        latitude=20.2961,
        longitude=85.8245,
        start_date="2026-08-25",
        end_date="2026-08-27",
    )

    assert len(historical.historical) == 3
    assert (
        historical.historical[0].temperature_max
        == 31.2
    )


def test_historical_date_validation():
    from app.openmeteo.client import OpenMeteoClient

    client = OpenMeteoClient()

    try:
        with pytest.raises(ValueError):
            asyncio.run(
                client.get_historical(
                    latitude=20.2961,
                    longitude=85.8245,
                    start_date="2026-08-27",
                    end_date="2026-08-25",
                )
            )
    finally:
        asyncio.run(client.close())