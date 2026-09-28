from app.models.weather import OpenMeteoResponse
from app.normalization.weather_normalizer import (
    CanonicalWeather,
    WeatherNormalizer,
)


def sample_openmeteo_response():
    return OpenMeteoResponse.model_validate(
        {
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
                "time": "2026-08-28T18:45",
                "interval": 900,
                "temperature_2m": 27.4,
                "relative_humidity_2m": 92,
                "apparent_temperature": 33.4,
                "precipitation": 0.0,
                "rain": 0.0,
                "weather_code": 3,
                "cloud_cover": 99,
                "surface_pressure": 997.3,
                "wind_speed_10m": 8.9,
                "wind_direction_10m": 251,
                "wind_gusts_10m": 16.6,
            },
        }
    )


def test_normalize_openmeteo_response():
    source_data = sample_openmeteo_response()

    weather = WeatherNormalizer.normalize(source_data)

    assert isinstance(weather, CanonicalWeather)
    assert weather.latitude == 20.281195
    assert weather.longitude == 85.843376
    assert weather.temperature == 27.4
    assert weather.relative_humidity == 92
    assert weather.wind_speed == 8.9
    assert weather.wind_direction == 251
    assert weather.source == "open-meteo"


def test_normalized_timestamp():
    source_data = sample_openmeteo_response()

    weather = WeatherNormalizer.normalize(source_data)

    assert weather.observed_at.year == 2026
    assert weather.observed_at.month == 8
    assert weather.observed_at.day == 28


def test_normalized_weather_contains_all_core_values():
    source_data = sample_openmeteo_response()

    weather = WeatherNormalizer.normalize(source_data)

    assert weather.apparent_temperature == 33.4
    assert weather.precipitation == 0.0
    assert weather.rain == 0.0
    assert weather.weather_code == 3
    assert weather.cloud_cover == 99
    assert weather.surface_pressure == 997.3
    assert weather.wind_gusts == 16.6