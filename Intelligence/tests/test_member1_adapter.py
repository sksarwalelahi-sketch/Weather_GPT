"""
Tests for the Member 1 -> Member 3 integration adapter.
"""

from datetime import datetime

from integration.member1_adapter import (
    current_to_weather_input,
    forecast_to_weather_inputs,
    historical_to_climate_values,
)


# ---------------------------------------------------------------------
# Actual Member 1 Current Response
# ---------------------------------------------------------------------

CURRENT_RESPONSE = {
    "latitude": 20.281195,
    "longitude": 85.843376,
    "observed_at": "2026-09-05T16:45:00",
    "temperature": 27.3,
    "apparent_temperature": 33.5,
    "relative_humidity": 93,
    "precipitation": 0,
    "rain": 0,
    "weather_code": 0,
    "cloud_cover": 14,
    "surface_pressure": 1004.6,
    "wind_speed": 8.3,
    "wind_direction": 210,
    "wind_gusts": 14.8,
    "source": "open-meteo",
}


# ---------------------------------------------------------------------
# Actual Member 1 Forecast Response
# ---------------------------------------------------------------------

FORECAST_RESPONSE = {
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
            "wind_speed_max": 12,
        },
        {
            "date": "2026-09-07",
            "temperature_max": 31.7,
            "temperature_min": 25.9,
            "precipitation": 9.7,
            "rain": 3.3,
            "weather_code": 96,
            "wind_speed_max": 12,
        },
        {
            "date": "2026-09-08",
            "temperature_max": 32.8,
            "temperature_min": 25.1,
            "precipitation": 9.3,
            "rain": 2.8,
            "weather_code": 96,
            "wind_speed_max": 10.9,
        },
        {
            "date": "2026-09-09",
            "temperature_max": 32.1,
            "temperature_min": 25.3,
            "precipitation": 20.7,
            "rain": 7.4,
            "weather_code": 96,
            "wind_speed_max": 9.4,
        },
        {
            "date": "2026-09-10",
            "temperature_max": 30.1,
            "temperature_min": 23.9,
            "precipitation": 28.1,
            "rain": 5.2,
            "weather_code": 96,
            "wind_speed_max": 11.8,
        },
        {
            "date": "2026-09-11",
            "temperature_max": 30.6,
            "temperature_min": 24,
            "precipitation": 10.8,
            "rain": 4.2,
            "weather_code": 95,
            "wind_speed_max": 10.6,
        },
    ],
}


# ---------------------------------------------------------------------
# Actual Member 1 Historical Response
# ---------------------------------------------------------------------

HISTORICAL_RESPONSE = {
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
            "wind_speed_max": 16,
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
        {
            "date": "2026-08-20",
            "temperature_max": 33.1,
            "temperature_min": 26.9,
            "precipitation": 2.7,
            "rain": 2.7,
            "weather_code": 55,
            "wind_speed_max": 12.5,
        },
    ],
}


# ---------------------------------------------------------------------
# Current Adapter Tests
# ---------------------------------------------------------------------


def test_current_to_weather_input():
    weather = current_to_weather_input(
        CURRENT_RESPONSE,
        location_name="Bhubaneswar",
    )

    assert weather.latitude == 20.281195
    assert weather.longitude == 85.843376

    assert weather.timestamp == datetime(
        2026,
        9,
        5,
        16,
        45,
    )

    assert weather.temperature == 27.3
    assert weather.feels_like == 33.5
    assert weather.humidity == 93
    assert weather.pressure == 1004.6

    # Confirm M1 rain -> M3 rainfall
    assert weather.rainfall == 0

    assert weather.wind_speed == 8.3
    assert weather.wind_direction == 210
    assert weather.wind_gust == 14.8

    assert weather.source == "open-meteo"
    assert weather.location_name == "Bhubaneswar"

    # These are intentionally unavailable from M1.
    assert weather.precipitation_probability is None
    assert weather.visibility is None
    assert weather.forecast_horizon_hours is None


def test_current_adapter_does_not_use_precipitation_as_probability():
    payload = dict(CURRENT_RESPONSE)

    payload["precipitation"] = 25.0
    payload["rain"] = 7.5

    weather = current_to_weather_input(payload)

    assert weather.rainfall == 7.5
    assert weather.precipitation_probability is None


# ---------------------------------------------------------------------
# Forecast Adapter Tests
# ---------------------------------------------------------------------


def test_forecast_to_weather_inputs():
    weather_points = forecast_to_weather_inputs(
        FORECAST_RESPONSE,
        location_name="Bhubaneswar",
    )

    assert len(weather_points) == 7

    first = weather_points[0]

    assert first.latitude == 20.281195
    assert first.longitude == 85.843376

    assert first.timestamp == datetime(
        2026,
        9,
        5,
        0,
        0,
    )

    # Daily-risk modeling decision:
    # temperature_max -> temperature
    assert first.temperature == 32.2

    # M1 rain -> M3 rainfall
    assert first.rainfall == 1.7

    # Daily-risk modeling decision:
    # wind_speed_max -> wind_speed
    assert first.wind_speed == 8.5

    assert first.source == "open-meteo"

    assert first.feels_like is None
    assert first.humidity is None
    assert first.pressure is None
    assert first.wind_direction is None
    assert first.wind_gust is None
    assert first.visibility is None
    assert first.precipitation_probability is None


def test_forecast_adapter_uses_rain_not_precipitation():
    weather_points = forecast_to_weather_inputs(
        FORECAST_RESPONSE,
    )

    fifth = weather_points[4]

    # Actual M1 values:
    # precipitation = 20.7
    # rain = 7.4
    assert fifth.rainfall == 7.4
    assert fifth.rainfall != 20.7

    assert fifth.precipitation_probability is None


def test_forecast_adapter_preserves_chronological_order():
    weather_points = forecast_to_weather_inputs(
        FORECAST_RESPONSE,
    )

    timestamps = [
        weather.timestamp
        for weather in weather_points
    ]

    assert timestamps == sorted(timestamps)


def test_forecast_adapter_handles_empty_forecast():
    payload = dict(FORECAST_RESPONSE)
    payload["forecast"] = []

    weather_points = forecast_to_weather_inputs(payload)

    assert weather_points == []


# ---------------------------------------------------------------------
# Historical Adapter Tests
# ---------------------------------------------------------------------


def test_historical_to_climate_values():
    baselines = {
        "temperature": 30.0,
        "rainfall": 5.0,
        "wind_speed": 15.0,
    }

    historical_values = historical_to_climate_values(
        HISTORICAL_RESPONSE,
        baselines=baselines,
    )

    assert set(historical_values.keys()) == {
        "temperature",
        "rainfall",
        "wind_speed",
    }

    assert historical_values["temperature"]["values"] == [
        29.8,
        32.8,
        33.1,
    ]

    assert historical_values["rainfall"]["values"] == [
        13.6,
        3.6,
        2.7,
    ]

    assert historical_values["wind_speed"]["values"] == [
        16,
        15.7,
        12.5,
    ]

    assert historical_values["temperature"]["baseline"] == 30.0
    assert historical_values["rainfall"]["baseline"] == 5.0
    assert historical_values["wind_speed"]["baseline"] == 15.0

    assert (
        historical_values["temperature"]["period"]
        == "2026-08-18 to 2026-08-20"
    )


def test_historical_adapter_does_not_create_humidity():
    baselines = {
        "temperature": 30.0,
        "rainfall": 5.0,
        "wind_speed": 15.0,
    }

    historical_values = historical_to_climate_values(
        HISTORICAL_RESPONSE,
        baselines=baselines,
    )

    assert "humidity" not in historical_values