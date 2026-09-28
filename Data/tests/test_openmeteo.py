import pytest

from app.openmeteo.client import OpenMeteoClient
from app.models.weather import CurrentWeather, OpenMeteoResponse
from app.models.weather import CurrentWeather
from pydantic import ValidationError

@pytest.mark.integration
@pytest.mark.asyncio
async def test_openmeteo_client_creation():
    client = OpenMeteoClient()

    assert client.client is not None

    await client.close()


@pytest.mark.asyncio
async def test_get_weather():
    client = OpenMeteoClient()

    try:
        weather = await client.get_weather(
            latitude=20.2961,
            longitude=85.8245,
        )

        assert isinstance(weather, OpenMeteoResponse)
        assert weather.current.temperature is not None

    finally:
        await client.close()
        
        
def test_current_weather_model():
    data = {
        "time": "2026-08-28T17:45",
        "temperature_2m": 27.1,
        "relative_humidity_2m": 95,
        "apparent_temperature": 33.3,
        "precipitation": 0.0,
        "rain": 0.0,
        "weather_code": 3,
        "cloud_cover": 99,
        "surface_pressure": 997.9,
        "wind_speed_10m": 9.0,
        "wind_direction_10m": 255,
        "wind_gusts_10m": 16.6,
    }

    weather = CurrentWeather.model_validate(data)

    assert weather.temperature == 27.1
    assert weather.relative_humidity == 95
    assert weather.wind_speed == 9.0
    assert weather.weather_code == 3
    
def test_current_weather_rejects_invalid_temperature():
    data = {
        "time": "2026-08-28T17:45",
        "temperature_2m": "not-a-temperature",
        "relative_humidity_2m": 95,
        "apparent_temperature": 33.3,
        "precipitation": 0.0,
        "rain": 0.0,
        "weather_code": 3,
        "cloud_cover": 99,
        "surface_pressure": 997.9,
        "wind_speed_10m": 9.0,
        "wind_direction_10m": 255,
        "wind_gusts_10m": 16.6,
    }

    with pytest.raises(ValidationError):
        CurrentWeather.model_validate(data)
        
def test_openmeteo_response_model():
    data = {
        "latitude": 20.281195,
        "longitude": 85.843376,
        "generationtime_ms": 0.2117,
        "utc_offset_seconds": 0,
        "timezone": "GMT",
        "timezone_abbreviation": "GMT",
        "elevation": 44.0,
        "current_units": {
            "time": "iso8601",
            "interval": "seconds",
            "temperature_2m": "°C",
            "relative_humidity_2m": "%",
            "apparent_temperature": "°C",
            "precipitation": "mm",
            "rain": "mm",
            "weather_code": "wmo code",
            "cloud_cover": "%",
            "surface_pressure": "hPa",
            "wind_speed_10m": "km/h",
            "wind_direction_10m": "°",
            "wind_gusts_10m": "km/h",
        },
        "current": {
            "time": "2026-08-28T17:45",
            "interval": 900,
            "temperature_2m": 27.1,
            "relative_humidity_2m": 95,
            "apparent_temperature": 33.3,
            "precipitation": 0.0,
            "rain": 0.0,
            "weather_code": 3,
            "cloud_cover": 99,
            "surface_pressure": 997.9,
            "wind_speed_10m": 9.0,
            "wind_direction_10m": 255,
            "wind_gusts_10m": 16.6,
        },
    }

    weather = OpenMeteoResponse.model_validate(data)

    assert weather.latitude == 20.281195
    assert weather.longitude == 85.843376
    assert weather.current.temperature == 27.1
    assert weather.current.relative_humidity == 95