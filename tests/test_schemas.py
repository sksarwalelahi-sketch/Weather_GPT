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

# ---------------------------------------------------------------------------
# Member 3 - Risk Engine Data Quality Tests
# ---------------------------------------------------------------------------

from intelligence.risk import assess_weather_risk
from schemas.risk import DataQuality


def test_risk_engine_complete_data():
    """
    All three core weather measurements are available.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        temperature=34.0,
        rainfall=20.0,
        wind_speed=30.0,
        source="MOCK",
    )

    result = assess_weather_risk(weather)

    assert result.data_quality == DataQuality.COMPLETE
    assert result.confidence == 1.0
    assert len(result.components) == 3


def test_risk_engine_partial_data():
    """
    Only two of the three core weather measurements are available.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        temperature=34.0,
        rainfall=20.0,
        source="MOCK",
    )

    result = assess_weather_risk(weather)

    assert result.data_quality == DataQuality.PARTIAL
    assert result.confidence == 0.67
    assert len(result.components) == 2


def test_risk_engine_single_measurement():
    """
    Only one core weather measurement is available.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        temperature=39.0,
        source="MOCK",
    )

    result = assess_weather_risk(weather)

    assert result.data_quality == DataQuality.PARTIAL
    assert result.confidence == 0.33
    assert len(result.components) == 1


def test_risk_engine_insufficient_data():
    """
    None of the core weather measurements are available.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        source="MOCK",
    )

    result = assess_weather_risk(weather)

    assert result.data_quality == DataQuality.INSUFFICIENT
    assert result.confidence == 0.0
    assert result.overall_score == 0.0
    assert len(result.components) == 0


def test_risk_engine_overall_risk_uses_highest_component():
    """
    Overall risk should reflect the highest individual
    component risk.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        temperature=34.0,
        rainfall=50.0,
        wind_speed=30.0,
        source="MOCK",
    )

    result = assess_weather_risk(weather)

    assert result.overall_level == RiskLevel.HIGH
    assert result.overall_score == 62.5

    # ---------------------------------------------------------------------------
# Member 3 - Hazard Orchestrator Tests
# ---------------------------------------------------------------------------

from intelligence.hazard import detect_hazards


def test_hazard_orchestrator_returns_list():
    """
    Hazard orchestrator should always return a list of
    standardized hazard results.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        temperature=39.0,
        rainfall=65.0,
        wind_speed=72.0,
        source="MOCK",
    )

    result = detect_hazards(weather)

    assert isinstance(result, list)


def test_hazard_orchestrator_initially_returns_no_hazards():
    """
    Until individual hazard detectors are connected,
    the orchestrator should return an empty list.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        source="MOCK",
    )

    result = detect_hazards(weather)

    assert result == []

# ---------------------------------------------------------------------------
# Member 3 - Heavy Rainfall Hazard Detector Tests
# ---------------------------------------------------------------------------

from intelligence.heavy_rain import detect_heavy_rainfall
from schemas.hazard import HazardType


def test_heavy_rainfall_detector_ignores_moderate_rainfall():
    """
    Moderate rainfall should not create a heavy-rainfall hazard.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        rainfall=20.0,
        source="MOCK",
    )

    result = detect_heavy_rainfall(weather)

    assert result is None


def test_heavy_rainfall_detector_detects_high_rainfall():
    """
    High rainfall should create a HIGH heavy-rainfall hazard.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        rainfall=50.0,
        source="MOCK",
    )

    result = detect_heavy_rainfall(weather)

    assert result is not None
    assert result.hazard_type == HazardType.HEAVY_RAINFALL
    assert result.severity == RiskLevel.HIGH
    assert result.score == 62.5
    assert result.confidence == 1.0


def test_heavy_rainfall_detector_detects_severe_rainfall():
    """
    Severe rainfall should create a SEVERE heavy-rainfall hazard.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        rainfall=80.0,
        source="MOCK",
    )

    result = detect_heavy_rainfall(weather)

    assert result is not None
    assert result.hazard_type == HazardType.HEAVY_RAINFALL
    assert result.severity == RiskLevel.SEVERE
    assert result.score == 85.71
    assert result.confidence == 1.0


def test_heavy_rainfall_detector_handles_missing_rainfall():
    """
    Missing rainfall data should not produce a hazard.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        source="MOCK",
    )

    result = detect_heavy_rainfall(weather)



# ---------------------------------------------------------------------------
# Member 3 - Heatwave Hazard Detector Tests
# ---------------------------------------------------------------------------

from intelligence.heatwave import detect_heatwave
from schemas.hazard import HazardType


def test_heatwave_detector_ignores_moderate_temperature():
    """
    Moderate temperature should not create a heatwave hazard.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        temperature=34.0,
        source="MOCK",
    )

    result = detect_heatwave(weather)

    assert result is None


def test_heatwave_detector_detects_high_temperature():
    """
    High temperature should create a HIGH heatwave hazard.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        temperature=39.0,
        source="MOCK",
    )

    result = detect_heatwave(weather)

    assert result is not None
    assert result.hazard_type == HazardType.HEATWAVE
    assert result.severity == RiskLevel.HIGH
    assert result.score == 66.67
    assert result.confidence == 1.0


def test_heatwave_detector_detects_severe_temperature():
    """
    Severe temperature should create a SEVERE heatwave hazard.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        temperature=42.0,
        source="MOCK",
    )

    result = detect_heatwave(weather)

    assert result is not None
    assert result.hazard_type == HazardType.HEATWAVE
    assert result.severity == RiskLevel.SEVERE
    assert result.score == 85.0
    assert result.confidence == 1.0


def test_heatwave_detector_handles_missing_temperature():
    """
    Missing temperature should not produce a heatwave hazard.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        source="MOCK",
    )

    result = detect_heatwave(weather)

    assert result is None


def test_heatwave_detector_threshold_boundaries():
    """
    Verify the HIGH and SEVERE heatwave boundaries.
    """

    high_weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        temperature=37.0,
        source="MOCK",
    )

    severe_weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        temperature=40.0,
        source="MOCK",
    )

    high_result = detect_heatwave(high_weather)
    severe_result = detect_heatwave(severe_weather)

    assert high_result is not None
    assert high_result.severity == RiskLevel.HIGH

    assert severe_result is not None
    assert severe_result.severity == RiskLevel.SEVERE

# ---------------------------------------------------------------------------
# Member 3 - Cyclone Hazard Detector Tests
# ---------------------------------------------------------------------------

from intelligence.cyclone import detect_cyclone


def test_cyclone_detector_rejects_strong_wind_without_supporting_signal():
    """
    Strong wind alone should not be classified as a cyclone.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        wind_speed=70.0,
        source="MOCK",
    )

    result = detect_cyclone(weather)

    assert result is None


def test_cyclone_detector_detects_wind_and_low_pressure():
    """
    Strong wind combined with low pressure should produce
    a cyclone hazard.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        wind_speed=70.0,
        pressure=985.0,
        source="MOCK",
    )

    result = detect_cyclone(weather)

    assert result is not None
    assert result.hazard_type == HazardType.CYCLONE
    assert result.severity == RiskLevel.SEVERE
    assert result.score == 75.0
    assert result.confidence == 0.7


def test_cyclone_detector_detects_wind_and_heavy_rainfall():
    """
    Strong wind combined with heavy rainfall should produce
    a cyclone hazard.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        wind_speed=70.0,
        rainfall=70.0,
        source="MOCK",
    )

    result = detect_cyclone(weather)

    assert result is not None
    assert result.hazard_type == HazardType.CYCLONE
    assert result.severity == RiskLevel.SEVERE
    assert result.score == 75.0
    assert result.confidence == 0.7


def test_cyclone_detector_detects_wind_and_high_humidity():
    """
    Strong wind combined with high humidity should produce
    a cyclone screening result.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        wind_speed=65.0,
        humidity=85.0,
        source="MOCK",
    )

    result = detect_cyclone(weather)

    assert result is not None
    assert result.hazard_type == HazardType.CYCLONE
    assert result.severity == RiskLevel.HIGH
    assert result.score == 70.0
    assert result.confidence == 0.7


def test_cyclone_detector_handles_normal_weather():
    """
    Normal weather conditions should not produce a cyclone hazard.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        wind_speed=25.0,
        pressure=1012.0,
        rainfall=5.0,
        humidity=60.0,
        source="MOCK",
    )

    result = detect_cyclone(weather)

    assert result is None


def test_cyclone_detector_uses_wind_gust_and_pressure():
    """
    Strong wind gust plus low pressure should be sufficient
    for cyclone screening.
    """

    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        wind_speed=45.0,
        wind_gust=95.0,
        pressure=988.0,
        source="MOCK",
    )

    result = detect_cyclone(weather)

    assert result is not None
    assert result.hazard_type == HazardType.CYCLONE
    assert result.severity == RiskLevel.SEVERE
    assert result.score == 80.0

# ---------------------------------------------------------------------------
# Member 3 - Flood Hazard Detector Tests
# ---------------------------------------------------------------------------

from intelligence.flood import detect_flood


def test_flood_detector_returns_none_for_low_rainfall():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        rainfall=20.0,
        source="MOCK",
    )

    result = detect_flood(weather)

    assert result is None


def test_flood_detector_returns_none_for_heavy_rain_without_supporting_signal():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        rainfall=50.0,
        source="MOCK",
    )

    result = detect_flood(weather)

    assert result is None


def test_flood_detector_detects_heavy_rain_with_high_probability():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        rainfall=50.0,
        precipitation_probability=90.0,
        source="MOCK",
    )

    result = detect_flood(weather)

    assert result is not None
    assert result.hazard_type == HazardType.FLOOD
    assert result.severity == RiskLevel.HIGH
    assert result.score == 65.0
    assert result.confidence == 0.9


def test_flood_detector_detects_very_heavy_rainfall():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        rainfall=80.0,
        source="MOCK",
    )

    result = detect_flood(weather)

    assert result is not None
    assert result.hazard_type == HazardType.FLOOD
    assert result.severity == RiskLevel.HIGH
    assert result.score == 60.0
    assert result.confidence == 0.7


def test_flood_detector_detects_severe_rainfall():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        rainfall=110.0,
        source="MOCK",
    )

    result = detect_flood(weather)

    assert result is not None
    assert result.hazard_type == HazardType.FLOOD
    assert result.severity == RiskLevel.SEVERE
    assert result.score == 75.0
    assert result.confidence == 0.7


def test_flood_detector_combines_rainfall_and_probability():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        rainfall=110.0,
        precipitation_probability=90.0,
        source="MOCK",
    )

    result = detect_flood(weather)

    assert result is not None
    assert result.hazard_type == HazardType.FLOOD
    assert result.severity == RiskLevel.SEVERE
    assert result.score == 95.0
    assert result.confidence == 0.9


def test_flood_detector_returns_none_when_rainfall_is_missing():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        source="MOCK",
    )

    result = detect_flood(weather)

    assert result is None

# ---------------------------------------------------------------------------
# Member 3 - Extreme Wind Hazard Detector Tests
# ---------------------------------------------------------------------------

from intelligence.extreme_wind import detect_extreme_wind


def test_extreme_wind_detector_returns_none_for_moderate_wind():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        wind_speed=30.0,
        source="MOCK",
    )

    result = detect_extreme_wind(weather)

    assert result is None


def test_extreme_wind_detector_detects_high_wind():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        wind_speed=50.0,
        source="MOCK",
    )

    result = detect_extreme_wind(weather)

    assert result is not None
    assert result.hazard_type == HazardType.EXTREME_WIND
    assert result.severity == RiskLevel.HIGH
    assert result.score == 62.5
    assert result.confidence == 1.0


def test_extreme_wind_detector_detects_severe_wind():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        wind_speed=80.0,
        source="MOCK",
    )

    result = detect_extreme_wind(weather)

    assert result is not None
    assert result.hazard_type == HazardType.EXTREME_WIND
    assert result.severity == RiskLevel.SEVERE
    assert result.score == 91.67
    assert result.confidence == 1.0


def test_extreme_wind_detector_uses_wind_gust():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        wind_speed=45.0,
        wind_gust=95.0,
        source="MOCK",
    )

    result = detect_extreme_wind(weather)

    assert result is not None
    assert result.hazard_type == HazardType.EXTREME_WIND
    assert result.severity == RiskLevel.SEVERE
    assert result.score == 100.0
    assert result.confidence == 1.0


def test_extreme_wind_detector_returns_none_when_wind_missing():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        source="MOCK",
    )

    result = detect_extreme_wind(weather)

    assert result is None

# ---------------------------------------------------------------------------
# Member 3 - Hazard Orchestrator Tests
# ---------------------------------------------------------------------------

from intelligence.hazard import detect_hazards


def test_hazard_orchestrator_returns_empty_for_normal_weather():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        temperature=25.0,
        rainfall=2.0,
        wind_speed=10.0,
        pressure=1012.0,
        humidity=60.0,
        source="MOCK",
    )

    hazards = detect_hazards(weather)

    assert hazards == []


def test_hazard_orchestrator_detects_heavy_rain_and_flood():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        rainfall=80.0,
        source="MOCK",
    )

    hazards = detect_hazards(weather)

    hazard_types = {
        hazard.hazard_type
        for hazard in hazards
    }

    assert HazardType.HEAVY_RAINFALL in hazard_types
    assert HazardType.FLOOD in hazard_types


def test_hazard_orchestrator_detects_multiple_hazards():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        temperature=42.0,
        rainfall=110.0,
        wind_speed=80.0,
        wind_gust=95.0,
        pressure=985.0,
        humidity=85.0,
        source="MOCK",
    )

    hazards = detect_hazards(weather)

    hazard_types = {
        hazard.hazard_type
        for hazard in hazards
    }

    assert HazardType.HEAVY_RAINFALL in hazard_types
    assert HazardType.HEATWAVE in hazard_types
    assert HazardType.CYCLONE in hazard_types
    assert HazardType.FLOOD in hazard_types
    assert HazardType.EXTREME_WIND in hazard_types

    assert len(hazards) == 5


def test_hazard_orchestrator_returns_standardized_results():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        rainfall=80.0,
        wind_speed=70.0,
        source="MOCK",
    )

    hazards = detect_hazards(weather)

    assert len(hazards) >= 1

    for hazard in hazards:
        assert isinstance(hazard, HazardResult)
        assert 0 <= hazard.score <= 100
        assert 0 <= hazard.confidence <= 1
        assert hazard.reason

from schemas.alert import AlertStatus
from intelligence.alerts import generate_alert, generate_alerts


def test_generate_alert_for_heavy_rainfall():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        rainfall=80.0,
        location_name="Bhubaneswar",
        source="MOCK",
    )

    hazards = detect_hazards(weather)
    rainfall_hazard = next(
        h for h in hazards
        if h.hazard_type == HazardType.HEAVY_RAINFALL
    )

    alert = generate_alert(rainfall_hazard)

    assert alert.alert_type == HazardType.HEAVY_RAINFALL
    assert alert.severity == RiskLevel.SEVERE
    assert alert.status == AlertStatus.ACTIVE
    assert alert.location_name == "Bhubaneswar"
    assert alert.title == "Severe Heavy Rainfall Warning"
    assert alert.recommended_action
    assert alert.valid_until > alert.valid_from
    assert alert.source == "WeatherGPT Intelligence Engine"


def test_generate_alert_uses_unknown_location_when_missing():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        rainfall=80.0,
        source="MOCK",
    )

    hazards = detect_hazards(weather)
    alerts = generate_alerts(hazards)

    assert alerts

    for alert in alerts:
        assert alert.location_name == "Unknown Location"


def test_generate_alerts_matches_hazards():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        temperature=42.0,
        rainfall=110.0,
        wind_speed=80.0,
        wind_gust=95.0,
        pressure=985.0,
        humidity=85.0,
        location_name="Bhubaneswar",
        source="MOCK",
    )

    hazards = detect_hazards(weather)
    alerts = generate_alerts(hazards)

    assert len(alerts) == len(hazards)

    for hazard, alert in zip(hazards, alerts):
        assert alert.alert_type == hazard.hazard_type
        assert alert.severity == hazard.severity
        assert alert.status == AlertStatus.ACTIVE

from schemas.advisory import AdvisoryDomain, AdvisoryPriority
from intelligence.advisory import generate_advisory, generate_advisories

def test_generate_advisory_for_heavy_rainfall():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        rainfall=50.0,
        location_name="Bhubaneswar",
        source="MOCK",
    )

    hazards = detect_hazards(weather)

    hazard = next(
        h for h in hazards
        if h.hazard_type == HazardType.HEAVY_RAINFALL
    )

    advisory = generate_advisory(hazard)

    assert advisory.domain == AdvisoryDomain.GENERAL
    assert advisory.priority == AdvisoryPriority.HIGH
    assert advisory.risk_level == RiskLevel.HIGH
    assert advisory.location_name == "Bhubaneswar"
    assert advisory.title == "Heavy Rainfall Advisory"
    assert advisory.message
    assert len(advisory.actions) > 0
    assert advisory.valid_until > advisory.issued_at
    assert advisory.source == "WeatherGPT Intelligence Engine"


def test_generate_advisory_unknown_location():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        rainfall=80.0,
        source="MOCK",
    )

    hazards = detect_hazards(weather)
    advisories = generate_advisories(hazards)

    assert advisories

    for advisory in advisories:
        assert advisory.location_name == "Unknown Location"


def test_generate_advisories_matches_detected_hazards():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        temperature=42.0,
        rainfall=110.0,
        wind_speed=80.0,
        wind_gust=95.0,
        pressure=985.0,
        humidity=85.0,
        location_name="Bhubaneswar",
        source="MOCK",
    )

    hazards = detect_hazards(weather)
    advisories = generate_advisories(hazards)

    assert len(advisories) == len(hazards)

    for hazard, advisory in zip(hazards, advisories):
        assert advisory.risk_level == hazard.severity
        assert advisory.location_name == hazard.location_name


def test_no_advisories_when_no_hazards():
    weather = WeatherInput(
        latitude=20.0,
        longitude=85.0,
        timestamp=datetime.now(),
        temperature=25.0,
        rainfall=2.0,
        wind_speed=10.0,
        source="MOCK",
    )

    hazards = detect_hazards(weather)
    advisories = generate_advisories(hazards)

    assert hazards == []
    assert advisories == []