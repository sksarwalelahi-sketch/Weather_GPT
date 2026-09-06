"""
WeatherGPT - Member 3
Weather Risk Engine

This module converts validated weather observations into
explainable weather-risk assessments.

Current capabilities:
- Rainfall risk
- Wind risk
- Heat risk
- Overall risk aggregation
- Data-quality classification
- Input-data coverage confidence

The engine is deterministic and explainable.

IMPORTANT:
The baseline thresholds in this module are engineering
development values. They are not represented as official
IMD warning thresholds.
"""

from __future__ import annotations

from schemas.risk import (
    DataQuality,
    RiskAssessment,
    RiskComponent,
    RiskLevel,
)
from schemas.weather import WeatherInput

from intelligence.thresholds import (
    RAINFALL,
    TEMPERATURE,
    WIND_SPEED,
)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def _level_from_thresholds(
    value: float,
    thresholds,
) -> RiskLevel:
    """
    Convert a numeric weather value into a categorical risk level.

    Threshold interpretation:

        value < low
            -> LOW

        low <= value < moderate
            -> MODERATE

        moderate <= value < high
            -> HIGH

        value >= high
            -> SEVERE
    """

    if value < thresholds.low:
        return RiskLevel.LOW

    if value < thresholds.moderate:
        return RiskLevel.MODERATE

    if value < thresholds.high:
        return RiskLevel.HIGH

    return RiskLevel.SEVERE


def _score_from_thresholds(
    value: float,
    thresholds,
) -> float:
    """
    Convert a weather measurement into a normalized 0-100 score.

    The score increases continuously between the configured
    threshold boundaries.
    """

    if value <= 0:
        return 0.0

    low = thresholds.low
    moderate = thresholds.moderate
    high = thresholds.high
    severe = thresholds.severe

    if value < low:
        return (value / low) * 25.0

    if value < moderate:
        return 25.0 + (
            (value - low) / (moderate - low)
        ) * 25.0

    if value < high:
        return 50.0 + (
            (value - moderate) / (high - moderate)
        ) * 25.0

    if value < severe:
        return 75.0 + (
            (value - high) / (severe - high)
        ) * 25.0

    return 100.0


# ---------------------------------------------------------------------------
# Rainfall risk
# ---------------------------------------------------------------------------


def calculate_rainfall_risk(
    rainfall: float,
) -> RiskComponent:
    """
    Calculate rainfall-related risk.

    Parameters
    ----------
    rainfall:
        Rainfall amount in millimetres.
    """

    level = _level_from_thresholds(
        rainfall,
        RAINFALL,
    )

    score = _score_from_thresholds(
        rainfall,
        RAINFALL,
    )

    if level == RiskLevel.LOW:
        reason = (
            f"Rainfall of {rainfall:.1f} mm is within "
            "the low-risk range."
        )

    elif level == RiskLevel.MODERATE:
        reason = (
            f"Rainfall of {rainfall:.1f} mm may cause "
            "localized water accumulation."
        )

    elif level == RiskLevel.HIGH:
        reason = (
            f"Rainfall of {rainfall:.1f} mm indicates "
            "heavy rainfall conditions."
        )

    else:
        reason = (
            f"Rainfall of {rainfall:.1f} mm indicates "
            "very heavy rainfall conditions with elevated "
            "waterlogging and flooding potential."
        )

    return RiskComponent(
        risk_type="rainfall",
        level=level,
        score=round(score, 2),
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Wind risk
# ---------------------------------------------------------------------------


def calculate_wind_risk(
    wind_speed: float,
) -> RiskComponent:
    """
    Calculate wind-related risk.

    Parameters
    ----------
    wind_speed:
        Wind speed in km/h.
    """

    level = _level_from_thresholds(
        wind_speed,
        WIND_SPEED,
    )

    score = _score_from_thresholds(
        wind_speed,
        WIND_SPEED,
    )

    if level == RiskLevel.LOW:
        reason = (
            f"Wind speed of {wind_speed:.1f} km/h is within "
            "the low-risk range."
        )

    elif level == RiskLevel.MODERATE:
        reason = (
            f"Wind speed of {wind_speed:.1f} km/h indicates "
            "moderately strong winds."
        )

    elif level == RiskLevel.HIGH:
        reason = (
            f"Wind speed of {wind_speed:.1f} km/h indicates "
            "strong winds with potential operational impacts."
        )

    else:
        reason = (
            f"Wind speed of {wind_speed:.1f} km/h indicates "
            "severe wind conditions with increased safety risks."
        )

    return RiskComponent(
        risk_type="wind",
        level=level,
        score=round(score, 2),
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Heat risk
# ---------------------------------------------------------------------------


def calculate_heat_risk(
    temperature: float,
) -> RiskComponent:
    """
    Calculate heat-related risk.

    Parameters
    ----------
    temperature:
        Air temperature in degrees Celsius.
    """

    level = _level_from_thresholds(
        temperature,
        TEMPERATURE,
    )

    score = _score_from_thresholds(
        temperature,
        TEMPERATURE,
    )

    if level == RiskLevel.LOW:
        reason = (
            f"Temperature of {temperature:.1f}°C is within "
            "the low-risk range."
        )

    elif level == RiskLevel.MODERATE:
        reason = (
            f"Temperature of {temperature:.1f}°C indicates "
            "moderate heat conditions."
        )

    elif level == RiskLevel.HIGH:
        reason = (
            f"Temperature of {temperature:.1f}°C indicates "
            "high heat stress potential."
        )

    else:
        reason = (
            f"Temperature of {temperature:.1f}°C indicates "
            "severe heat conditions."
        )

    return RiskComponent(
        risk_type="heat",
        level=level,
        score=round(score, 2),
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------


def _calculate_data_quality(
    weather: WeatherInput,
) -> tuple[DataQuality, float]:
    """
    Determine weather-data coverage and its associated
    input-coverage confidence.

    Current core measurements:

        temperature
        rainfall
        wind_speed

    Confidence is based only on availability of these fields.

    It is NOT the probability of a weather event.
    """

    core_values = [
        weather.temperature,
        weather.rainfall,
        weather.wind_speed,
    ]

    available_count = sum(
        value is not None
        for value in core_values
    )

    total_count = len(core_values)

    if available_count == 0:
        return DataQuality.INSUFFICIENT, 0.0

    if available_count == total_count:
        return DataQuality.COMPLETE, 1.0

    confidence = available_count / total_count

    return (
        DataQuality.PARTIAL,
        round(confidence, 2),
    )


# ---------------------------------------------------------------------------
# Overall risk aggregation
# ---------------------------------------------------------------------------


def _calculate_overall_level(
    components: list[RiskComponent],
) -> RiskLevel:
    """
    Determine overall risk from individual components.

    The highest individual risk currently determines the
    overall categorical risk.
    """

    if not components:
        return RiskLevel.LOW

    priority = {
        RiskLevel.LOW: 0,
        RiskLevel.MODERATE: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.SEVERE: 3,
    }

    return max(
        components,
        key=lambda component: priority[component.level],
    ).level


def _calculate_overall_score(
    components: list[RiskComponent],
) -> float:
    """
    Calculate the overall numeric risk score.

    The highest component score is used for the first version
    of the engine.
    """

    if not components:
        return 0.0

    return round(
        max(component.score for component in components),
        2,
    )


# ---------------------------------------------------------------------------
# Main risk assessment
# ---------------------------------------------------------------------------


def assess_weather_risk(
    weather: WeatherInput,
) -> RiskAssessment:
    """
    Generate a complete weather risk assessment.

    Available measurements are evaluated independently.

    Current supported measurements:

        rainfall
        wind_speed
        temperature
    """

    components: list[RiskComponent] = []

    if weather.rainfall is not None:
        components.append(
            calculate_rainfall_risk(
                weather.rainfall
            )
        )

    if weather.wind_speed is not None:
        components.append(
            calculate_wind_risk(
                weather.wind_speed
            )
        )

    if weather.temperature is not None:
        components.append(
            calculate_heat_risk(
                weather.temperature
            )
        )

    data_quality, confidence = _calculate_data_quality(
        weather
    )

    overall_level = _calculate_overall_level(
        components
    )

    overall_score = _calculate_overall_score(
        components
    )

    return RiskAssessment(
        overall_level=overall_level,
        overall_score=overall_score,
        components=components,
        data_quality=data_quality,
        confidence=confidence,
        location_name=weather.location_name,
        timestamp=weather.timestamp,
    )