"""
Tests for the Member 3 Intelligence Service.
"""

from datetime import date
from unittest.mock import Mock

from integration.member1_client import Member1Client
from schemas.forecast import ForecastAnalysis
from schemas.intelligence import WeatherIntelligenceResult
from services.intelligence_service import IntelligenceService


CURRENT_PAYLOAD = {
    "latitude": 20.281195,
    "longitude": 85.843376,
    "observed_at": "2026-09-05T18:15:00",
    "temperature": 27.3,
    "apparent_temperature": 33.8,
    "relative_humidity": 95,
    "precipitation": 0,
    "rain": 0,
    "weather_code": 0,
    "cloud_cover": 15,
    "surface_pressure": 1004.4,
    "wind_speed": 8.2,
    "wind_direction": 218,
    "wind_gusts": 14.8,
    "source": "open-meteo",
}


FORECAST_PAYLOAD = {
    "latitude": 20.281195,
    "longitude": 85.843376,
    "timezone": "GMT",
    "source": "open-meteo",
    "forecast": [
        {
            "date": "2026-09-05",
            "temperature_max": 32.2,
            "temperature_min": 26.4,
            "precipitation": 3.1,
            "rain": 1.7,
            "weather_code": 95,
            "wind_speed_max": 8.5,
        },
        {
            "date": "2026-09-06",
            "temperature_max": 33.3,
            "temperature_min": 26.3,
            "precipitation": 3.2,
            "rain": 1.4,
            "weather_code": 95,
            "wind_speed_max": 12.0,
        },
    ],
}


HISTORICAL_PAYLOAD = {
    "latitude": 20.281195,
    "longitude": 85.843376,
    "timezone": "GMT",
    "source": "open-meteo",
    "start_date": "2026-08-18",
    "end_date": "2026-08-20",
    "historical": [
        {
            "date": "2026-08-18",
            "temperature_max": 29.8,
            "temperature_min": 24.8,
            "precipitation": 13.6,
            "rain": 13.6,
            "weather_code": 63,
            "wind_speed_max": 16.0,
        },
        {
            "date": "2026-08-19",
            "temperature_max": 32.8,
            "temperature_min": 25.3,
            "precipitation": 3.6,
            "rain": 3.6,
            "weather_code": 55,
            "wind_speed_max": 15.7,
        },
    ],
}


def make_service() -> tuple[IntelligenceService, Mock]:
    client = Mock(spec=Member1Client)
    service = IntelligenceService(client=client)
    return service, client


def test_analyze_current():
    service, client = make_service()

    client.get_current.return_value = CURRENT_PAYLOAD

    result = service.analyze_current(
        latitude=20.281195,
        longitude=85.843376,
        location_name="Bhubaneswar",
    )

    assert isinstance(result, WeatherIntelligenceResult)
    assert result.location_name == "Bhubaneswar"
    assert result.risk_assessment is not None

    client.get_current.assert_called_once_with(
        latitude=20.281195,
        longitude=85.843376,
    )


def test_analyze_forecast():
    service, client = make_service()

    client.get_forecast.return_value = FORECAST_PAYLOAD

    result = service.analyze_forecast(
        latitude=20.281195,
        longitude=85.843376,
        forecast_days=7,
        location_name="Bhubaneswar",
    )

    assert isinstance(result, ForecastAnalysis)
    assert result.location_name == "Bhubaneswar"
    assert result.data_points == 2
    assert len(result.forecast_points) == 2

    client.get_forecast.assert_called_once_with(
        latitude=20.281195,
        longitude=85.843376,
        forecast_days=7,
    )


def test_analyze_current_with_history():
    service, client = make_service()

    client.get_current.return_value = CURRENT_PAYLOAD
    client.get_historical.return_value = HISTORICAL_PAYLOAD

    result = service.analyze_current_with_history(
        latitude=20.281195,
        longitude=85.843376,
        start_date=date(2026, 8, 18),
        end_date=date(2026, 8, 20),
        baselines={
            "temperature": 30.0,
            "rainfall": 10.0,
            "wind_speed": 15.0,
        },
        location_name="Bhubaneswar",
    )

    assert isinstance(result, WeatherIntelligenceResult)
    assert result.location_name == "Bhubaneswar"
    assert len(result.climate_analysis) == 3

    client.get_current.assert_called_once_with(
        latitude=20.281195,
        longitude=85.843376,
    )

    client.get_historical.assert_called_once_with(
        latitude=20.281195,
        longitude=85.843376,
        start_date=date(2026, 8, 18),
        end_date=date(2026, 8, 20),
    )


def test_get_current_data():
    service, client = make_service()

    client.get_current.return_value = CURRENT_PAYLOAD

    result = service.get_current_data(
        latitude=20.281195,
        longitude=85.843376,
    )

    assert result == CURRENT_PAYLOAD


def test_get_forecast_data():
    service, client = make_service()

    client.get_forecast.return_value = FORECAST_PAYLOAD

    result = service.get_forecast_data(
        latitude=20.281195,
        longitude=85.843376,
        forecast_days=5,
    )

    assert result == FORECAST_PAYLOAD


def test_get_historical_data():
    service, client = make_service()

    client.get_historical.return_value = HISTORICAL_PAYLOAD

    result = service.get_historical_data(
        latitude=20.281195,
        longitude=85.843376,
        start_date=date(2026, 8, 18),
        end_date=date(2026, 8, 20),
    )

    assert result == HISTORICAL_PAYLOAD