"""
WeatherGPT - Member 3
Decision Engine Tests
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
    location_name="Delhi",
    source="TEST_SOURCE",
):
    if timestamp is None:
        timestamp = datetime(2026, 8, 28, 12, 0)

    return WeatherInput(
        location_name=location_name,
        latitude=28.6139,
        longitude=77.2090,
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


def test_analyze_weather_basic():
    weather = make_weather()

    result = analyze_weather(weather)

    assert result.location_name == "Delhi"
    assert result.risk_assessment is not None
    assert result.risk_assessment.overall_level == RiskLevel.LOW
    assert result.hazards == []
    assert result.alerts == []
    assert result.advisories == []
    assert result.climate_analysis == []


def test_analyze_weather_detects_hazards_alerts_and_advisories():
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

    assert len(result.hazards) == 5
    assert len(result.alerts) == 5
    assert len(result.advisories) > 5


def test_analyze_weather_generates_domain_advisories():
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

    domains = {
        advisory.domain.value
        for advisory in result.advisories
    }

    assert "GENERAL" in domains
    assert "AGRICULTURE" in domains
    assert "AVIATION" in domains
    assert "MARINE" in domains


def test_analyze_weather_with_climate_analysis():
    weather = make_weather()

    historical_values = {
        "temperature": {
            "values": [30.0, 31.0, 32.0, 33.0],
            "baseline": 30.0,
            "period": "Last 4 days",
        },
        "rainfall": {
            "values": [5.0, 10.0, 15.0, 20.0],
            "baseline": 10.0,
            "period": "Last 4 days",
        },
    }

    result = analyze_weather(
        weather,
        historical_values=historical_values,
    )

    assert len(result.climate_analysis) == 2

    metrics = {
        analysis.metric.value
        for analysis in result.climate_analysis
    }

    assert "TEMPERATURE" in metrics
    assert "RAINFALL" in metrics


def test_analyze_weather_ignores_unknown_climate_metric():
    weather = make_weather()

    historical_values = {
        "temperature": {
            "values": [30.0, 31.0],
            "baseline": 30.0,
            "period": "Test period",
        },
        "unknown_metric": {
            "values": [1.0, 2.0],
            "baseline": 1.0,
            "period": "Test period",
        },
    }

    result = analyze_weather(
        weather,
        historical_values=historical_values,
    )

    assert len(result.climate_analysis) == 1
    assert result.climate_analysis[0].metric.value == "TEMPERATURE"


def test_analyze_weather_handles_missing_climate_configuration():
    weather = make_weather()

    historical_values = {
        "temperature": {
            "values": [],
            "baseline": 30.0,
            "period": "Test period",
        },
        "rainfall": {
            "values": [10.0, 20.0],
            "period": "Test period",
        },
    }

    result = analyze_weather(
        weather,
        historical_values=historical_values,
    )

    assert result.climate_analysis == []


def test_analyze_weather_unknown_location():
    weather = make_weather(location_name=None)

    result = analyze_weather(weather)

    assert result.location_name == "Unknown Location"


def test_analyze_weather_batch():
    timestamp = datetime(2026, 8, 28, 12, 0)

    weather_points = [
        make_weather(timestamp=timestamp),
        make_weather(
            timestamp=timestamp + timedelta(hours=1),
            temperature=39.0,
        ),
        make_weather(
            timestamp=timestamp + timedelta(hours=2),
            rainfall=80.0,
            precipitation_probability=90.0,
        ),
    ]

    results = analyze_weather_batch(weather_points)

    assert len(results) == 3
    assert all(result.location_name == "Delhi" for result in results)

    assert results[0].risk_assessment is not None
    assert results[1].risk_assessment is not None
    assert results[2].risk_assessment is not None


def test_analyze_weather_batch_empty():
    with pytest.raises(
        ValueError,
        match="At least one weather observation is required",
    ):
        analyze_weather_batch([])


def test_get_decision_summary():
    weather = make_weather(
        temperature=39.0,
        rainfall=50.0,
        wind_speed=50.0,
    )

    result = analyze_weather(weather)
    summary = get_decision_summary(result)

    assert summary["location"] == "Delhi"
    assert summary["risk_level"] == result.risk_assessment.overall_level.value
    assert summary["risk_score"] == result.risk_assessment.overall_score
    assert summary["hazard_count"] == len(result.hazards)
    assert summary["alert_count"] == len(result.alerts)
    assert summary["advisory_count"] == len(result.advisories)
    assert summary["climate_analysis_count"] == 0
    assert "generated_at" in summary


def test_get_decision_summary_with_climate():
    weather = make_weather()

    result = analyze_weather(
        weather,
        historical_values={
            "temperature": {
                "values": [30.0, 31.0, 32.0],
                "baseline": 30.0,
                "period": "Test period",
            }
        },
    )

    summary = get_decision_summary(result)

    assert summary["climate_analysis_count"] == 1


def test_decision_engine_preserves_weather_location():
    weather = make_weather(location_name="Bhubaneswar")

    result = analyze_weather(weather)

    assert result.location_name == "Bhubaneswar"
    assert result.risk_assessment.location_name == "Bhubaneswar"