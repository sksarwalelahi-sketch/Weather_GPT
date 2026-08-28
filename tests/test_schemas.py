"""
WeatherGPT - Member 3
Schema Test Suite

Automated tests for all internal WeatherGPT intelligence schemas.
"""

import sys
from pathlib import Path

# Add the WeatherGPT project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from schemas.weather import WeatherInput
from schemas.risk import (
    RiskAssessment,
    RiskComponent,
    RiskLevel,
)
from schemas.hazard import (
    HazardResult,
    HazardType,
)
from schemas.alert import (
    AlertResult,
    AlertStatus,
)
from schemas.advisory import (
    AdvisoryDomain,
    AdvisoryPriority,
    AdvisoryResult,
)
from schemas.climate import (
    ClimateAnalysis,
    ClimateMetric,
    TrendDirection,
)
from schemas.intelligence import WeatherIntelligenceResult


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

@pytest.fixture
def timestamp():
    """Provide a consistent timestamp for tests."""
    return datetime(2026, 8, 28, 12, 0, 0)


# ---------------------------------------------------------------------------
# WeatherInput tests
# ---------------------------------------------------------------------------

def test_weather_input_valid(timestamp):
    """Valid weather data should create a WeatherInput object."""

    weather = WeatherInput(
        location_name="Bhubaneswar",
        latitude=20.2961,
        longitude=85.8245,
        timestamp=timestamp,
        temperature=32,
        humidity=70,
        rainfall=10,
        wind_speed=25,
        source="MOCK",
    )

    assert weather.location_name == "Bhubaneswar"
    assert weather.temperature == 32
    assert weather.humidity == 70
    assert weather.rainfall == 10
    assert weather.wind_speed == 25


def test_weather_input_invalid_latitude(timestamp):
    """Latitude outside -90 to 90 should be rejected."""

    with pytest.raises(ValidationError):
        WeatherInput(
            latitude=200,
            longitude=85,
            timestamp=timestamp,
        )


def test_weather_input_invalid_longitude(timestamp):
    """Longitude outside -180 to 180 should be rejected."""

    with pytest.raises(ValidationError):
        WeatherInput(
            latitude=20,
            longitude=200,
            timestamp=timestamp,
        )


def test_weather_input_invalid_humidity(timestamp):
    """Humidity outside 0 to 100 should be rejected."""

    with pytest.raises(ValidationError):
        WeatherInput(
            latitude=20,
            longitude=85,
            timestamp=timestamp,
            humidity=150,
        )


# ---------------------------------------------------------------------------
# Risk schema tests
# ---------------------------------------------------------------------------

def test_risk_component_valid():
    """Valid risk component should be accepted."""

    risk = RiskComponent(
        risk_type="rainfall",
        level=RiskLevel.HIGH,
        score=85,
        reason="Heavy rainfall expected",
    )

    assert risk.risk_type == "rainfall"
    assert risk.level == RiskLevel.HIGH
    assert risk.score == 85


def test_risk_component_invalid_score():
    """Risk score above 100 should be rejected."""

    with pytest.raises(ValidationError):
        RiskComponent(
            risk_type="rainfall",
            level=RiskLevel.HIGH,
            score=150,
            reason="Invalid score",
        )


def test_risk_assessment():
    """RiskAssessment should contain its components correctly."""

    component = RiskComponent(
        risk_type="wind",
        level=RiskLevel.MODERATE,
        score=60,
        reason="Strong winds expected",
    )

    assessment = RiskAssessment(
        overall_level=RiskLevel.MODERATE,
        overall_score=60,
        components=[component],
        location_name="Bhubaneswar",
        timestamp=datetime.now(),
    )

    assert assessment.overall_level == RiskLevel.MODERATE
    assert assessment.overall_score == 60
    assert len(assessment.components) == 1


# ---------------------------------------------------------------------------
# Hazard schema tests
# ---------------------------------------------------------------------------

def test_hazard_result_valid(timestamp):
    """Valid hazard result should be accepted."""

    hazard = HazardResult(
        hazard_type=HazardType.CYCLONE,
        severity=RiskLevel.HIGH,
        score=88,
        confidence=0.92,
        reason="Cyclone conditions detected",
        location_name="Odisha Coast",
        timestamp=timestamp,
    )

    assert hazard.hazard_type == HazardType.CYCLONE
    assert hazard.severity == RiskLevel.HIGH
    assert hazard.score == 88
    assert hazard.confidence == 0.92


def test_hazard_invalid_confidence(timestamp):
    """Confidence above 1 should be rejected."""

    with pytest.raises(ValidationError):
        HazardResult(
            hazard_type=HazardType.FLOOD,
            severity=RiskLevel.HIGH,
            score=80,
            confidence=1.5,
            reason="Invalid confidence",
            timestamp=timestamp,
        )


# ---------------------------------------------------------------------------
# Alert schema tests
# ---------------------------------------------------------------------------

def test_alert_result_valid(timestamp):
    """Valid alert should be accepted."""

    alert = AlertResult(
        alert_type=HazardType.HEAVY_RAINFALL,
        severity=RiskLevel.HIGH,
        status=AlertStatus.ACTIVE,
        title="Heavy Rainfall Warning",
        description="Heavy rainfall expected.",
        location_name="Sambalpur",
        issued_at=timestamp,
        valid_from=timestamp,
        valid_until=timestamp + timedelta(hours=12),
        recommended_action="Avoid unnecessary travel.",
        source="MOCK",
    )

    assert alert.alert_type == HazardType.HEAVY_RAINFALL
    assert alert.severity == RiskLevel.HIGH
    assert alert.status == AlertStatus.ACTIVE


def test_alert_empty_title(timestamp):
    """An empty alert title should be rejected."""

    with pytest.raises(ValidationError):
        AlertResult(
            alert_type=HazardType.FLOOD,
            severity=RiskLevel.HIGH,
            title="",
            description="Flood warning",
            location_name="Sambalpur",
            issued_at=timestamp,
            valid_from=timestamp,
            valid_until=timestamp + timedelta(hours=6),
            recommended_action="Avoid flooded areas.",
        )


# ---------------------------------------------------------------------------
# Advisory schema tests
# ---------------------------------------------------------------------------

def test_agriculture_advisory(timestamp):
    """Agriculture advisory should be accepted."""

    advisory = AdvisoryResult(
        domain=AdvisoryDomain.AGRICULTURE,
        priority=AdvisoryPriority.HIGH,
        risk_level=RiskLevel.HIGH,
        title="Heavy Rainfall Advisory",
        message="Protect crops from heavy rainfall.",
        actions=[
            "Clear drainage channels",
            "Protect harvested crops",
        ],
        location_name="Sambalpur",
        issued_at=timestamp,
        valid_until=timestamp + timedelta(hours=12),
        source="MOCK",
    )

    assert advisory.domain == AdvisoryDomain.AGRICULTURE
    assert advisory.priority == AdvisoryPriority.HIGH
    assert len(advisory.actions) == 2


def test_invalid_advisory_priority(timestamp):
    """Unknown advisory priority should be rejected."""

    with pytest.raises(ValidationError):
        AdvisoryResult(
            domain=AdvisoryDomain.AGRICULTURE,
            priority="URGENT_UNKNOWN",
            risk_level=RiskLevel.HIGH,
            title="Test Advisory",
            message="Test message",
            location_name="Sambalpur",
            issued_at=timestamp,
        )


# ---------------------------------------------------------------------------
# Climate schema tests
# ---------------------------------------------------------------------------

def test_climate_analysis(timestamp):
    """Valid climate analysis should be accepted."""

    climate = ClimateAnalysis(
        metric=ClimateMetric.RAINFALL,
        period="2015-2025",
        average_value=1250,
        baseline_value=1100,
        anomaly=150,
        trend=TrendDirection.INCREASING,
        trend_percentage=13.64,
        confidence=0.88,
        location_name="Sambalpur",
        data_points=120,
    )

    assert climate.metric == ClimateMetric.RAINFALL
    assert climate.trend == TrendDirection.INCREASING
    assert climate.anomaly == 150
    assert climate.data_points == 120


def test_climate_invalid_confidence():
    """Climate confidence above 1 should be rejected."""

    with pytest.raises(ValidationError):
        ClimateAnalysis(
            metric=ClimateMetric.RAINFALL,
            period="2015-2025",
            average_value=1250,
            baseline_value=1100,
            anomaly=150,
            trend=TrendDirection.INCREASING,
            confidence=1.5,
            location_name="Sambalpur",
        )


# ---------------------------------------------------------------------------
# Unified intelligence result tests
# ---------------------------------------------------------------------------

def test_empty_intelligence_result(timestamp):
    """Unified result should support empty optional collections."""

    result = WeatherIntelligenceResult(
        location_name="Bhubaneswar",
        generated_at=timestamp,
    )

    assert result.location_name == "Bhubaneswar"
    assert result.risk_assessment is None
    assert result.hazards == []
    assert result.alerts == []
    assert result.advisories == []
    assert result.climate_analysis == []
    assert result.processing_version == "1.0.0"


def test_complete_intelligence_result(timestamp):
    """Unified result should correctly aggregate all intelligence outputs."""

    risk_component = RiskComponent(
        risk_type="rainfall",
        level=RiskLevel.HIGH,
        score=85,
        reason="Heavy rainfall expected",
    )

    risk = RiskAssessment(
        overall_level=RiskLevel.HIGH,
        overall_score=82,
        components=[risk_component],
        location_name="Bhubaneswar",
        timestamp=timestamp,
    )

    hazard = HazardResult(
        hazard_type=HazardType.HEAVY_RAINFALL,
        severity=RiskLevel.HIGH,
        score=85,
        confidence=0.91,
        reason="Heavy rainfall conditions detected",
        location_name="Bhubaneswar",
        timestamp=timestamp,
    )

    alert = AlertResult(
        alert_type=HazardType.HEAVY_RAINFALL,
        severity=RiskLevel.HIGH,
        title="Heavy Rainfall Warning",
        description="Heavy rainfall expected.",
        location_name="Bhubaneswar",
        issued_at=timestamp,
        valid_from=timestamp,
        valid_until=timestamp + timedelta(hours=12),
        recommended_action="Avoid unnecessary travel.",
        source="MOCK",
    )

    advisory = AdvisoryResult(
        domain=AdvisoryDomain.AGRICULTURE,
        priority=AdvisoryPriority.HIGH,
        risk_level=RiskLevel.HIGH,
        title="Agriculture Advisory",
        message="Protect crops from heavy rainfall.",
        actions=[
            "Clear drainage channels",
            "Protect harvested crops",
        ],
        location_name="Bhubaneswar",
        issued_at=timestamp,
        valid_until=timestamp + timedelta(hours=12),
        source="MOCK",
    )

    climate = ClimateAnalysis(
        metric=ClimateMetric.RAINFALL,
        period="2015-2025",
        average_value=1250,
        baseline_value=1100,
        anomaly=150,
        trend=TrendDirection.INCREASING,
        trend_percentage=13.64,
        confidence=0.88,
        location_name="Bhubaneswar",
        data_points=120,
    )

    result = WeatherIntelligenceResult(
        location_name="Bhubaneswar",
        generated_at=timestamp,
        risk_assessment=risk,
        hazards=[hazard],
        alerts=[alert],
        advisories=[advisory],
        climate_analysis=[climate],
    )

    assert result.risk_assessment is not None
    assert len(result.hazards) == 1
    assert len(result.alerts) == 1
    assert len(result.advisories) == 1
    assert len(result.climate_analysis) == 1