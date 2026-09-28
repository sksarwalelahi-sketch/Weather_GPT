"""
WeatherGPT - Member 3
Forecast Intelligence Engine

Processes future WeatherInput observations through the existing
risk and hazard intelligence engines.

The engine does not generate raw weather forecasts itself.
It analyses forecast data supplied by the data/NWP layer.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from intelligence.hazard import detect_hazards
from intelligence.risk import assess_weather_risk
from schemas.forecast import ForecastAnalysis, ForecastPoint
from schemas.risk import RiskLevel
from schemas.weather import WeatherInput


# ---------------------------------------------------------------------
# Risk ordering
# ---------------------------------------------------------------------

_RISK_PRIORITY = {
    RiskLevel.LOW: 0,
    RiskLevel.MODERATE: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.SEVERE: 3,
}


# ---------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------


def _get_maximum_risk_level(
    risk_levels: list[RiskLevel],
) -> RiskLevel:
    """
    Return the highest risk level from a list of risk levels.
    """

    if not risk_levels:
        return RiskLevel.LOW

    return max(
        risk_levels,
        key=lambda level: _RISK_PRIORITY[level],
    )


def _collect_unique_hazards(
    forecast_points: list[ForecastPoint],
):
    """
    Collect one representative hazard for each hazard type.

    When the same hazard occurs at multiple forecast times,
    the highest-scoring occurrence is retained.
    """

    unique_hazards = {}

    for point in forecast_points:
        for hazard in point.hazards:
            hazard_type = hazard.hazard_type

            existing = unique_hazards.get(hazard_type)

            if existing is None or hazard.score > existing.score:
                unique_hazards[hazard_type] = hazard

    return list(unique_hazards.values())


def _build_summary(
    location_name: str,
    forecast_points: list[ForecastPoint],
    maximum_risk_level: RiskLevel,
    maximum_risk_score: float,
    hazards,
) -> str:
    """
    Build a concise human-readable forecast summary.
    """

    if not forecast_points:
        return (
            f"No forecast observations are available for "
            f"{location_name}."
        )

    if hazards:
        hazard_names = ", ".join(
            hazard.hazard_type.value.replace("_", " ").title()
            for hazard in hazards
        )

        return (
            f"{location_name} forecast indicates "
            f"{maximum_risk_level.value.lower()} weather risk "
            f"with a maximum risk score of "
            f"{maximum_risk_score:.2f}. "
            f"Potential hazards: {hazard_names}."
        )

    return (
        f"{location_name} forecast indicates "
        f"{maximum_risk_level.value.lower()} weather risk "
        f"with a maximum risk score of "
        f"{maximum_risk_score:.2f}. "
        f"No major weather hazards were detected."
    )


def _calculate_confidence(
    forecast_points: list[ForecastPoint],
) -> float:
    """
    Calculate overall forecast-analysis confidence.

    The score represents the average confidence of the individual
    risk assessments and therefore reflects data coverage rather
    than probability of a weather event.
    """

    if not forecast_points:
        return 0.0

    confidences = [
        point.risk_assessment.confidence
        for point in forecast_points
        if point.risk_assessment is not None
    ]

    if not confidences:
        return 0.0

    return sum(confidences) / len(confidences)


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------


def analyze_forecast(
    weather_points: Iterable[WeatherInput],
    location_name: str | None = None,
) -> ForecastAnalysis:
    """
    Analyse a sequence of forecast weather observations.

    Parameters
    ----------
    weather_points:
        Forecast WeatherInput observations.

    location_name:
        Optional location override. If omitted, the location from
        the first forecast point is used. If that is unavailable,
        "Unknown Location" is used.

    Returns
    -------
    ForecastAnalysis
        Structured forecast intelligence result.

    Raises
    ------
    ValueError
        If no forecast observations are supplied.
    """

    observations = list(weather_points)

    if not observations:
        raise ValueError(
            "At least one forecast observation is required."
        )

    # Ensure chronological processing.
    observations.sort(
        key=lambda weather: weather.timestamp
    )

    resolved_location = (
        location_name
        or observations[0].location_name
        or "Unknown Location"
    )

    forecast_points: list[ForecastPoint] = []

    for weather in observations:
        risk = assess_weather_risk(weather)

        hazards = detect_hazards(weather)

        forecast_points.append(
            ForecastPoint(
                weather=weather,
                risk_assessment=risk,
                hazards=hazards,
            )
        )

    risk_levels = [
        point.risk_assessment.overall_level
        for point in forecast_points
        if point.risk_assessment is not None
    ]

    maximum_risk_level = _get_maximum_risk_level(
        risk_levels
    )

    maximum_risk_score = max(
        (
            point.risk_assessment.overall_score
            for point in forecast_points
            if point.risk_assessment is not None
        ),
        default=0.0,
    )

    hazards = _collect_unique_hazards(
        forecast_points
    )

    confidence = _calculate_confidence(
        forecast_points
    )

    summary = _build_summary(
        location_name=resolved_location,
        forecast_points=forecast_points,
        maximum_risk_level=maximum_risk_level,
        maximum_risk_score=maximum_risk_score,
        hazards=hazards,
    )

    sources = {
        weather.source
        for weather in observations
        if weather.source
    }

    if len(sources) == 1:
        source = next(iter(sources))
    elif len(sources) > 1:
        source = "MULTIPLE"
    else:
        source = None

    return ForecastAnalysis(
        location_name=resolved_location,
        generated_at=datetime.now(),
        forecast_start=observations[0].timestamp,
        forecast_end=observations[-1].timestamp,
        forecast_points=forecast_points,
        maximum_risk_level=maximum_risk_level.value,
        maximum_risk_score=maximum_risk_score,
        hazards=hazards,
        summary=summary,
        confidence=confidence,
        source=source,
        data_points=len(observations),
    )


# ---------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------


def analyze_single_forecast(
    weather: WeatherInput,
) -> ForecastAnalysis:
    """
    Analyse a single forecast observation.

    This is mainly useful for API integrations where one forecast
    record is received at a time.
    """

    return analyze_forecast(
        weather_points=[weather],
        location_name=weather.location_name,
    )