"""
WeatherGPT - Member 3
Forecast Analysis Schema Tests
"""

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from schemas.forecast import (
    ForecastAnalysis,
    ForecastPoint,
)
from schemas.hazard import HazardResult, HazardType
from schemas.risk import RiskAssessment, RiskLevel
from schemas.weather import WeatherInput


# ---------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------


@pytest.fixture
def timestamp():
    return datetime(2026, 8, 28, 12, 0, 0)


@pytest.fixture
def weather(timestamp):
    return WeatherInput(
        location_name="Bhubaneswar",
        latitude=20.2961,
        longitude=85.8245,
        timestamp=timestamp,
        temperature=32.0,
        rainfall=20.0,
        wind_speed=25.0,
        source="MOCK",
        forecast_horizon_hours=6,
    )


@pytest.fixture
def risk(timestamp):
    return RiskAssessment(
        overall_level=RiskLevel.MODERATE,
        overall_score=35.0,
        components=[],
        confidence=1.0,
        location_name="Bhubaneswar",
        timestamp=timestamp,
    )


@pytest.fixture
def hazard(timestamp):
    return HazardResult(
        hazard_type=HazardType.HEAVY_RAINFALL,
        severity=RiskLevel.HIGH,
        score=65.0,
        confidence=0.9,
        reason="Heavy rainfall expected.",
        location_name="Bhubaneswar",
        timestamp=timestamp,
    )


# ---------------------------------------------------------------------
# ForecastPoint tests
# ---------------------------------------------------------------------


def test_forecast_point_basic(weather, risk, hazard):
    """Forecast point should combine weather, risk and hazards."""

    point = ForecastPoint(
        weather=weather,
        risk_assessment=risk,
        hazards=[hazard],
    )

    assert point.weather.location_name == "Bhubaneswar"
    assert point.risk_assessment is not None
    assert point.risk_assessment.overall_level == RiskLevel.MODERATE
    assert len(point.hazards) == 1
    assert point.hazards[0].hazard_type == HazardType.HEAVY_RAINFALL


def test_forecast_point_defaults(weather):
    """Risk and hazards should have safe defaults."""

    point = ForecastPoint(
        weather=weather,
    )

    assert point.risk_assessment is None
    assert point.hazards == []


# ---------------------------------------------------------------------
# ForecastAnalysis tests
# ---------------------------------------------------------------------


def test_forecast_analysis_basic(
    timestamp,
    weather,
    risk,
    hazard,
):
    """Forecast analysis should aggregate forecast information."""

    point = ForecastPoint(
        weather=weather,
        risk_assessment=risk,
        hazards=[hazard],
    )

    result = ForecastAnalysis(
        location_name="Bhubaneswar",
        generated_at=timestamp,
        forecast_start=timestamp,
        forecast_end=timestamp + timedelta(hours=6),
        forecast_points=[point],
        maximum_risk_level="MODERATE",
        maximum_risk_score=35.0,
        hazards=[hazard],
        summary="Moderate weather risk expected.",
        confidence=0.9,
        source="MOCK",
        data_points=1,
    )

    assert result.location_name == "Bhubaneswar"
    assert result.forecast_start == timestamp
    assert result.forecast_end == timestamp + timedelta(hours=6)
    assert len(result.forecast_points) == 1
    assert result.maximum_risk_score == 35.0
    assert len(result.hazards) == 1
    assert result.confidence == 0.9
    assert result.data_points == 1


def test_forecast_analysis_empty_points(timestamp):
    """Forecast analysis can safely represent no forecast points."""

    result = ForecastAnalysis(
        location_name="Bhubaneswar",
        generated_at=timestamp,
        forecast_start=timestamp,
        forecast_end=timestamp,
        maximum_risk_level="LOW",
        maximum_risk_score=0.0,
        summary="No forecast observations available.",
    )

    assert result.forecast_points == []
    assert result.hazards == []
    assert result.maximum_risk_score == 0.0
    assert result.confidence == 0.0
    assert result.data_points == 0


# ---------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------


def test_forecast_analysis_rejects_invalid_score(timestamp):
    """Risk score above 100 should be rejected."""

    with pytest.raises(ValidationError):
        ForecastAnalysis(
            location_name="Bhubaneswar",
            generated_at=timestamp,
            forecast_start=timestamp,
            forecast_end=timestamp,
            maximum_risk_level="SEVERE",
            maximum_risk_score=101.0,
            summary="Invalid risk score.",
        )


def test_forecast_analysis_rejects_invalid_confidence(timestamp):
    """Confidence above 1 should be rejected."""

    with pytest.raises(ValidationError):
        ForecastAnalysis(
            location_name="Bhubaneswar",
            generated_at=timestamp,
            forecast_start=timestamp,
            forecast_end=timestamp,
            maximum_risk_level="HIGH",
            maximum_risk_score=70.0,
            summary="Invalid confidence.",
            confidence=1.5,
        )


def test_forecast_analysis_rejects_negative_data_points(timestamp):
    """Negative data point count should be rejected."""

    with pytest.raises(ValidationError):
        ForecastAnalysis(
            location_name="Bhubaneswar",
            generated_at=timestamp,
            forecast_start=timestamp,
            forecast_end=timestamp,
            maximum_risk_level="LOW",
            maximum_risk_score=0.0,
            summary="Invalid data point count.",
            data_points=-1,
        )


def test_forecast_analysis_requires_location(timestamp):
    """Location is required."""

    with pytest.raises(ValidationError):
        ForecastAnalysis(
            location_name="",
            generated_at=timestamp,
            forecast_start=timestamp,
            forecast_end=timestamp,
            maximum_risk_level="LOW",
            maximum_risk_score=0.0,
            summary="Test.",
        )


def test_forecast_analysis_requires_summary(timestamp):
    """Summary must not be empty."""

    with pytest.raises(ValidationError):
        ForecastAnalysis(
            location_name="Bhubaneswar",
            generated_at=timestamp,
            forecast_start=timestamp,
            forecast_end=timestamp,
            maximum_risk_level="LOW",
            maximum_risk_score=0.0,
            summary="",
        )


# ============================================================
# Forecast Intelligence Engine Tests
# ============================================================

from datetime import datetime, timedelta

import pytest

from intelligence.forecast import (
    analyze_forecast,
    analyze_single_forecast,
)
from schemas.risk import RiskLevel
from schemas.weather import WeatherInput


def make_weather(
    *,
    timestamp,
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


def test_analyze_forecast_basic():
    now = datetime(2026, 8, 28, 12, 0)

    weather_points = [
        make_weather(timestamp=now),
        make_weather(timestamp=now + timedelta(hours=1)),
    ]

    result = analyze_forecast(weather_points)

    assert result.location_name == "Delhi"
    assert result.data_points == 2
    assert len(result.forecast_points) == 2
    assert result.maximum_risk_level == RiskLevel.LOW.value
    assert result.maximum_risk_score == 19.53
    assert result.hazards == []
    assert result.confidence == 1.0
    assert result.source == "TEST_SOURCE"


def test_analyze_forecast_detects_risk():
    now = datetime(2026, 8, 28, 12, 0)

    weather_points = [
        make_weather(
            timestamp=now,
            temperature=34.0,
            rainfall=20.0,
            wind_speed=30.0,
        )
    ]

    result = analyze_forecast(weather_points)

    assert result.maximum_risk_level == RiskLevel.MODERATE.value
    assert result.maximum_risk_score == 37.5
    assert result.forecast_points[0].risk_assessment is not None
    assert (
        result.forecast_points[0].risk_assessment.overall_level
        == RiskLevel.MODERATE
    )


def test_analyze_forecast_detects_hazards():
    now = datetime(2026, 8, 28, 12, 0)

    weather_points = [
        make_weather(
            timestamp=now,
            rainfall=80.0,
            precipitation_probability=90.0,
        )
    ]

    result = analyze_forecast(weather_points)

    assert len(result.hazards) >= 1

    hazard_types = {hazard.hazard_type.value for hazard in result.hazards}

    assert "HEAVY_RAINFALL" in hazard_types
    assert "FLOOD" in hazard_types


def test_analyze_forecast_detects_multiple_hazards():
    now = datetime(2026, 8, 28, 12, 0)

    weather_points = [
        make_weather(
            timestamp=now,
            temperature=42.0,
            rainfall=110.0,
            precipitation_probability=90.0,
            wind_speed=80.0,
            wind_gust=95.0,
            humidity=85.0,
            pressure=985.0,
        )
    ]

    result = analyze_forecast(weather_points)

    assert len(result.hazards) == 5
    assert result.maximum_risk_level == RiskLevel.SEVERE.value

    hazard_types = {hazard.hazard_type.value for hazard in result.hazards}

    assert "HEAVY_RAINFALL" in hazard_types
    assert "FLOOD" in hazard_types
    assert "HEATWAVE" in hazard_types
    assert "EXTREME_WIND" in hazard_types
    assert "CYCLONE" in hazard_types


def test_analyze_forecast_sorts_by_timestamp():
    now = datetime(2026, 8, 28, 12, 0)

    later = make_weather(
        timestamp=now + timedelta(hours=2),
        temperature=35.0,
    )

    earlier = make_weather(
        timestamp=now,
        temperature=25.0,
    )

    middle = make_weather(
        timestamp=now + timedelta(hours=1),
        temperature=30.0,
    )

    result = analyze_forecast([later, earlier, middle])

    timestamps = [
        point.weather.timestamp
        for point in result.forecast_points
    ]

    assert timestamps == [now, now + timedelta(hours=1), now + timedelta(hours=2)]

    assert result.forecast_start == now
    assert result.forecast_end == now + timedelta(hours=2)


def test_analyze_forecast_location_override():
    now = datetime(2026, 8, 28, 12, 0)

    weather_points = [
        make_weather(
            timestamp=now,
            location_name="Delhi",
        )
    ]

    result = analyze_forecast(
        weather_points,
        location_name="Mumbai",
    )

    assert result.location_name == "Mumbai"


def test_analyze_forecast_multiple_sources():
    now = datetime(2026, 8, 28, 12, 0)

    weather_points = [
        make_weather(
            timestamp=now,
            source="SOURCE_A",
        ),
        make_weather(
            timestamp=now + timedelta(hours=1),
            source="SOURCE_B",
        ),
    ]

    result = analyze_forecast(weather_points)

    assert result.source == "MULTIPLE"


def test_analyze_forecast_unknown_location():
    now = datetime(2026, 8, 28, 12, 0)

    weather = make_weather(
        timestamp=now,
        location_name=None,
    )

    result = analyze_forecast([weather])

    assert result.location_name == "Unknown Location"


def test_analyze_forecast_empty_input():
    with pytest.raises(ValueError, match="At least one forecast observation"):
        analyze_forecast([])


def test_analyze_single_forecast():
    now = datetime(2026, 8, 28, 12, 0)

    weather = make_weather(
        timestamp=now,
        temperature=39.0,
        location_name="Jaipur",
    )

    result = analyze_single_forecast(weather)

    assert result.location_name == "Jaipur"
    assert result.data_points == 1
    assert len(result.forecast_points) == 1
    assert result.forecast_points[0].weather == weather


def test_analyze_forecast_confidence_is_averaged():
    now = datetime(2026, 8, 28, 12, 0)

    weather_points = [
        make_weather(
            timestamp=now,
            temperature=34.0,
        ),
        make_weather(
            timestamp=now + timedelta(hours=1),
            temperature=39.0,
        ),
    ]

    result = analyze_forecast(weather_points)

    confidences = [
        point.risk_assessment.confidence
        for point in result.forecast_points
        if point.risk_assessment is not None
    ]

    expected_confidence = sum(confidences) / len(confidences)

    assert result.confidence == pytest.approx(expected_confidence)


def test_analyze_forecast_summary_contains_location_and_risk():
    now = datetime(2026, 8, 28, 12, 0)

    weather_points = [
        make_weather(
            timestamp=now,
            temperature=39.0,
            rainfall=50.0,
            wind_speed=50.0,
        )
    ]

    result = analyze_forecast(weather_points)

    assert "Delhi" in result.summary
    assert "risk" in result.summary.lower()
    assert result.summary.strip() != ""