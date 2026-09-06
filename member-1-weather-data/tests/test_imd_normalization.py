from datetime import datetime, timezone

import pytest

from app.models.imd_weather import IMDWeather
from app.normalization.imd_normalizer import IMDWeatherNormalizer


def test_imd_normalizer_basic_payload():
    payload = {
        "latitude": 20.2961,
        "longitude": 85.8245,
        "timestamp": "2026-09-04T12:00:00Z",
        "temperature": 29.5,
        "relative_humidity": 72,
        "precipitation": 1.2,
        "wind_speed": 12.5,
        "wind_direction": 240,
        "pressure": 999.5,
        "station_id": "IMD-TEST-01",
    }

    weather = IMDWeatherNormalizer.normalize(payload)

    assert isinstance(weather, IMDWeather)
    assert weather.latitude == 20.2961
    assert weather.longitude == 85.8245
    assert weather.temperature == 29.5
    assert weather.relative_humidity == 72
    assert weather.precipitation == 1.2
    assert weather.wind_speed == 12.5
    assert weather.wind_direction == 240
    assert weather.pressure == 999.5
    assert weather.station_id == "IMD-TEST-01"
    assert weather.source == "imd"


def test_imd_normalizer_field_aliases():
    payload = {
        "lat": 20.2961,
        "lon": 85.8245,
        "time": "2026-09-04T12:00:00Z",
        "temp": 30.0,
        "rh": 70,
        "rainfall": 2.5,
        "wind_speed_10m": 10.0,
        "wind_direction_10m": 180,
        "surface_pressure": 1001.0,
        "station": "IMD-ALIAS-01",
    }

    weather = IMDWeatherNormalizer.normalize(payload)

    assert weather.latitude == 20.2961
    assert weather.longitude == 85.8245
    assert weather.temperature == 30.0
    assert weather.relative_humidity == 70
    assert weather.precipitation == 2.5
    assert weather.wind_speed == 10.0
    assert weather.wind_direction == 180
    assert weather.pressure == 1001.0
    assert weather.station_id == "IMD-ALIAS-01"


def test_imd_normalizer_nested_data():
    payload = {
        "data": {
            "latitude": 20.2961,
            "longitude": 85.8245,
            "timestamp": "2026-09-04T12:00:00Z",
            "temperature": 28.0,
            "relative_humidity": 80,
        }
    }

    weather = IMDWeatherNormalizer.normalize(payload)

    assert weather.latitude == 20.2961
    assert weather.longitude == 85.8245
    assert weather.temperature == 28.0
    assert weather.relative_humidity == 80
    assert weather.source == "imd"


def test_imd_normalizer_defaults_timestamp_and_source():
    payload = {
        "latitude": 20.2961,
        "longitude": 85.8245,
        "temperature": 27.0,
    }

    before = datetime.now(timezone.utc)

    weather = IMDWeatherNormalizer.normalize(payload)

    after = datetime.now(timezone.utc)

    assert weather.source == "imd"
    assert weather.timestamp.tzinfo is not None
    assert before <= weather.timestamp <= after


def test_imd_normalizer_rejects_invalid_payload():
    with pytest.raises(TypeError):
        IMDWeatherNormalizer.normalize("invalid")


def test_imd_normalizer_validates_coordinates():
    payload = {
        "latitude": 100,
        "longitude": 85.8245,
        "temperature": 30.0,
    }

    with pytest.raises(ValueError):
        IMDWeatherNormalizer.normalize(payload)