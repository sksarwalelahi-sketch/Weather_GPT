"""
WeatherGPT - Member 1 -> Member 3 Integration Tests

Validates the complete integration flow:

Member 1 API JSON
        ↓
Member 3 Adapter
        ↓
WeatherInput / historical_values
        ↓
Member 3 Intelligence Engine
        ↓
Risk + Hazards + Alerts + Advisories + Climate
"""

from intelligence.decision import analyze_weather
from intelligence.forecast import analyze_forecast

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
# 1. CURRENT → DECISION ENGINE
# ---------------------------------------------------------------------


def test_member1_current_to_m3_decision_engine():
    """
    Verify that an actual M1 current-weather response can travel
    through the complete M3 decision engine.
    """

    weather = current_to_weather_input(
        CURRENT_RESPONSE,
        location_name="Bhubaneswar",
    )

    result = analyze_weather(weather)

    assert result.location_name == "Bhubaneswar"

    assert result.risk_assessment is not None

    assert result.risk_assessment.timestamp == weather.timestamp

    assert result.risk_assessment.location_name == "Bhubaneswar"

    assert isinstance(result.hazards, list)
    assert isinstance(result.alerts, list)
    assert isinstance(result.advisories, list)
    assert isinstance(result.climate_analysis, list)

    assert result.processing_version == "1.0.0"


# ---------------------------------------------------------------------
# 2. CURRENT → VERIFY REAL FIELD SEMANTICS
# ---------------------------------------------------------------------
def test_member1_current_rain_mapping_reaches_risk_engine():
    """
    Verify that M1 rain is mapped to M3 rainfall and reaches
    the risk engine without being interpreted as precipitation
    probability.
    """

    payload = dict(CURRENT_RESPONSE)

    payload["rain"] = 50.0
    payload["precipitation"] = 100.0

    weather = current_to_weather_input(payload)

    assert weather.rainfall == 50.0
    assert weather.precipitation_probability is None

    result = analyze_weather(weather)

    assert result.risk_assessment is not None

    # The important integration contract is that the value
    # reaches WeatherInput as rainfall. The risk engine should
    # therefore produce a non-zero overall risk assessment.
    assert result.risk_assessment.overall_score > 0
# ---------------------------------------------------------------------
# 3. FORECAST → FORECAST INTELLIGENCE
# ---------------------------------------------------------------------


def test_member1_forecast_to_m3_forecast_analysis():
    """
    Verify that the actual M1 daily forecast response can be
    converted and analysed by the M3 forecast engine.
    """

    weather_points = forecast_to_weather_inputs(
        FORECAST_RESPONSE,
        location_name="Bhubaneswar",
    )

    result = analyze_forecast(
        weather_points,
        location_name="Bhubaneswar",
    )

    assert result.location_name == "Bhubaneswar"

    assert result.data_points == 7

    assert len(result.forecast_points) == 7

    assert result.forecast_start < result.forecast_end

    assert result.maximum_risk_score >= 0
    assert result.maximum_risk_score <= 100

    assert result.confidence >= 0
    assert result.confidence <= 1

    assert result.source == "open-meteo"

    assert result.summary


# ---------------------------------------------------------------------
# 4. FORECAST → VERIFY MAX TEMPERATURE MODEL
# ---------------------------------------------------------------------


def test_member1_forecast_uses_temperature_max_for_risk():
    """
    Verify the explicit M3 modeling decision:

        M1 temperature_max → M3 temperature
    """

    weather_points = forecast_to_weather_inputs(
        FORECAST_RESPONSE,
    )

    second = weather_points[1]

    assert second.temperature == 33.3

    result = analyze_forecast(weather_points)

    analysed_second = result.forecast_points[1]

    assert analysed_second.weather.temperature == 33.3

    assert analysed_second.risk_assessment is not None


# ---------------------------------------------------------------------
# 5. FORECAST → RAIN SEMANTICS
# ---------------------------------------------------------------------


def test_member1_forecast_rain_reaches_hazard_engine():
    """
    Verify that M1 rain, rather than precipitation, is used
    as M3 rainfall.
    """

    weather_points = forecast_to_weather_inputs(
        FORECAST_RESPONSE,
    )

    fifth = weather_points[4]

    assert fifth.rainfall == 7.4

    assert fifth.precipitation_probability is None

    result = analyze_forecast(weather_points)

    assert result.forecast_points[4].weather.rainfall == 7.4


# ---------------------------------------------------------------------
# 6. FORECAST → MISSING FIELDS REMAIN MISSING
# ---------------------------------------------------------------------


def test_member1_forecast_does_not_invent_missing_weather_data():
    """
    M1 daily forecast does not provide humidity, pressure,
    gusts, direction, visibility, or precipitation probability.

    The adapter must not invent those values.
    """

    weather_points = forecast_to_weather_inputs(
        FORECAST_RESPONSE,
    )

    for weather in weather_points:
        assert weather.humidity is None
        assert weather.pressure is None
        assert weather.wind_direction is None
        assert weather.wind_gust is None
        assert weather.visibility is None
        assert weather.precipitation_probability is None


# ---------------------------------------------------------------------
# 7. HISTORICAL → CLIMATE → DECISION ENGINE
# ---------------------------------------------------------------------


def test_member1_historical_to_m3_climate_analysis():
    """
    Verify the complete historical-data path:

        M1 historical JSON
        → climate input structure
        → M3 decision engine
        → climate analysis
    """

    baselines = {
        "temperature": 30.0,
        "rainfall": 5.0,
        "wind_speed": 15.0,
    }

    historical_values = historical_to_climate_values(
        HISTORICAL_RESPONSE,
        baselines=baselines,
    )

    weather = current_to_weather_input(
        CURRENT_RESPONSE,
        location_name="Bhubaneswar",
    )

    result = analyze_weather(
        weather,
        historical_values=historical_values,
    )

    assert len(result.climate_analysis) == 3

    metrics = {
        analysis.metric.value
        for analysis in result.climate_analysis
    }

    assert metrics == {
        "TEMPERATURE",
        "RAINFALL",
        "WIND_SPEED",
    }


# ---------------------------------------------------------------------
# 8. HISTORICAL → VERIFY VALUES
# ---------------------------------------------------------------------


def test_member1_historical_values_are_preserved():
    """
    Verify that the historical adapter preserves the actual
    M1 values without converting them into unrelated metrics.
    """

    baselines = {
        "temperature": 30.0,
        "rainfall": 5.0,
        "wind_speed": 15.0,
    }

    historical_values = historical_to_climate_values(
        HISTORICAL_RESPONSE,
        baselines=baselines,
    )

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

    assert "humidity" not in historical_values