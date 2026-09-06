"""
WeatherGPT - Member 3
End-to-End Intelligence Pipeline Tests

These tests verify that weather observations pass through the
complete intelligence pipeline and produce a unified decision.
"""

from datetime import datetime, timedelta

import pytest

from intelligence.decision import (
    analyze_weather,
    analyze_weather_batch,
    get_decision_summary,
)
from schemas.risk import RiskLevel
from schemas.weather import WeatherInput


def make_weather(
    *,
    timestamp=None,
    temperature=25.0,
    rainfall=2.0,
    wind_speed=10.0,
    wind_gust=15.0,
    humidity=60.0,
    pressure=1013.0,
    precipitation_probability=10.0,
    location_name="Bhubaneswar",
    source="E2E_TEST",
):
    if timestamp is None:
        timestamp = datetime(2026, 9, 2, 10, 0)

    return WeatherInput(
        location_name=location_name,
        latitude=20.2961,
        longitude=85.8245,
        timestamp=timestamp,
        temperature=temperature,
        humidity=humidity,
        pressure=pressure,
        rainfall=rainfall,
        precipitation_probability=precipitation_probability,
        wind_speed=wind_speed,
        wind_direction=180.0,
        wind_gust=wind_gust,
        visibility=10.0,
        source=source,
    )


# ============================================================
# NORMAL WEATHER
# ============================================================


def test_end_to_end_normal_weather():
    """
    Normal weather should produce a low-risk decision with
    no major hazards, alerts, or advisories.
    """

    weather = make_weather()

    result = analyze_weather(weather)

    assert result.location_name == "Bhubaneswar"

    assert result.risk_assessment is not None
    assert result.risk_assessment.overall_level == RiskLevel.LOW

    assert result.hazards == []
    assert result.alerts == []
    assert result.advisories == []
    assert result.climate_analysis == []


# ============================================================
# MODERATE WEATHER
# ============================================================


def test_end_to_end_moderate_weather():
    """
    Moderate weather should produce measurable risk while
    remaining below severe conditions.
    """

    weather = make_weather(
        temperature=34.0,
        rainfall=20.0,
        wind_speed=30.0,
    )

    result = analyze_weather(weather)

    assert result.risk_assessment is not None

    assert result.risk_assessment.overall_level == RiskLevel.MODERATE
    assert result.risk_assessment.overall_score == 37.5

    assert result.location_name == "Bhubaneswar"


# ============================================================
# HEAVY RAIN + FLOOD
# ============================================================


def test_end_to_end_heavy_rain_and_flood():
    """
    Heavy rainfall with high precipitation probability should
    propagate through risk, hazard, alert, and advisory layers.
    """

    weather = make_weather(
        rainfall=80.0,
        precipitation_probability=90.0,
    )

    result = analyze_weather(weather)

    assert result.risk_assessment is not None

    hazard_types = {
        hazard.hazard_type.value
        for hazard in result.hazards
    }

    assert "HEAVY_RAINFALL" in hazard_types
    assert "FLOOD" in hazard_types

    assert len(result.alerts) >= 2
    assert len(result.advisories) >= 2


# ============================================================
# EXTREME WEATHER
# ============================================================


def test_end_to_end_extreme_weather():
    """
    A combined extreme-weather scenario should trigger the
    complete hazard and response pipeline.
    """

    weather = make_weather(
        temperature=42.0,
        rainfall=110.0,
        precipitation_probability=90.0,
        wind_speed=80.0,
        wind_gust=95.0,
        humidity=85.0,
        pressure=985.0,
    )

    result = analyze_weather(weather)

    assert result.risk_assessment is not None
    assert result.risk_assessment.overall_level == RiskLevel.SEVERE

    # Five Member 3 hazard detectors should trigger.
    assert len(result.hazards) == 5

    hazard_types = {
        hazard.hazard_type.value
        for hazard in result.hazards
    }

    assert "CYCLONE" in hazard_types
    assert "FLOOD" in hazard_types
    assert "HEAVY_RAINFALL" in hazard_types
    assert "HEATWAVE" in hazard_types
    assert "EXTREME_WIND" in hazard_types

    # Each detected hazard should produce an alert.
    assert len(result.alerts) == 5

    # General + domain-specific advisories should be generated.
    assert len(result.advisories) > 5


# ============================================================
# CLIMATE + CURRENT WEATHER
# ============================================================


def test_end_to_end_weather_with_climate_analysis():
    """
    Current weather and historical climate intelligence should
    coexist in one unified decision result.
    """

    weather = make_weather(
        temperature=35.0,
        rainfall=30.0,
        wind_speed=25.0,
    )

    historical_values = {
        "temperature": {
            "values": [30.0, 31.0, 32.0, 34.0, 35.0],
            "baseline": 30.0,
            "period": "Last 5 days",
        },
        "rainfall": {
            "values": [5.0, 10.0, 15.0, 20.0, 30.0],
            "baseline": 10.0,
            "period": "Last 5 days",
        },
        "humidity": {
            "values": [60.0, 62.0, 64.0, 66.0, 68.0],
            "baseline": 60.0,
            "period": "Last 5 days",
        },
        "wind_speed": {
            "values": [10.0, 12.0, 14.0, 16.0, 18.0],
            "baseline": 12.0,
            "period": "Last 5 days",
        },
    }

    result = analyze_weather(
        weather,
        historical_values=historical_values,
    )

    assert result.risk_assessment is not None
    assert len(result.climate_analysis) == 4

    metrics = {
        analysis.metric.value
        for analysis in result.climate_analysis
    }

    assert metrics == {
        "TEMPERATURE",
        "RAINFALL",
        "HUMIDITY",
        "WIND_SPEED",
    }


# ============================================================
# BATCH PIPELINE
# ============================================================


def test_end_to_end_batch_processing():
    """
    Multiple observations should each produce a complete
    WeatherIntelligenceResult.
    """

    start = datetime(2026, 9, 2, 10, 0)

    weather_points = [
        make_weather(
            timestamp=start,
            temperature=25.0,
        ),
        make_weather(
            timestamp=start + timedelta(hours=1),
            temperature=34.0,
            rainfall=20.0,
            wind_speed=30.0,
        ),
        make_weather(
            timestamp=start + timedelta(hours=2),
            temperature=42.0,
            rainfall=110.0,
            precipitation_probability=90.0,
            wind_speed=80.0,
            wind_gust=95.0,
            humidity=85.0,
            pressure=985.0,
        ),
    ]

    results = analyze_weather_batch(weather_points)

    assert len(results) == 3

    assert results[0].risk_assessment.overall_level == RiskLevel.LOW

    assert results[1].risk_assessment.overall_level == RiskLevel.MODERATE

    assert results[2].risk_assessment.overall_level == RiskLevel.SEVERE

    assert len(results[2].hazards) == 5
    assert len(results[2].alerts) == 5


# ============================================================
# DECISION SUMMARY
# ============================================================


def test_end_to_end_decision_summary():
    """
    The final decision summary should expose the key information
    needed by a frontend/API consumer.
    """

    weather = make_weather(
        temperature=42.0,
        rainfall=110.0,
        precipitation_probability=90.0,
        wind_speed=80.0,
        wind_gust=95.0,
        humidity=85.0,
        pressure=985.0,
    )

    result = analyze_weather(weather)

    summary = get_decision_summary(result)

    assert summary["location"] == "Bhubaneswar"
    assert summary["risk_level"] == "SEVERE"
    assert summary["risk_score"] == result.risk_assessment.overall_score
    assert summary["hazard_count"] == 5
    assert summary["alert_count"] == 5
    assert summary["advisory_count"] == len(result.advisories)
    assert summary["climate_analysis_count"] == 0
    assert "generated_at" in summary


# ============================================================
# SOURCE PROPAGATION
# ============================================================


def test_end_to_end_source_propagation():
    """
    Weather source information should remain available in the
    generated intelligence objects.
    """

    weather = make_weather(
        source="NWP_MODEL_TEST",
        temperature=39.0,
        rainfall=50.0,
        wind_speed=50.0,
    )

    result = analyze_weather(weather)

    assert result.risk_assessment is not None
    assert result.risk_assessment.confidence > 0

    assert all(
        hazard.location_name == "Bhubaneswar"
        for hazard in result.hazards
    )


# ============================================================
# EMPTY BATCH SAFETY
# ============================================================


def test_end_to_end_empty_batch_rejected():
    """
    Empty input should fail explicitly instead of silently
    producing an invalid intelligence result.
    """

    with pytest.raises(
        ValueError,
        match="At least one weather observation is required",
    ):
        analyze_weather_batch([])