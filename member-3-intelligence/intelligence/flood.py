"""
WeatherGPT - Member 3
Flood Hazard Detector

Provides a first-pass, rule-based flood hazard screening
using the weather information currently available in
WeatherInput.

The detector primarily uses rainfall and precipitation
probability as indicators of potential flood conditions.

This is a screening detector and is not intended to replace
a hydrological flood model or an official flood warning.
"""

from __future__ import annotations

from schemas.hazard import HazardResult, HazardType
from schemas.risk import RiskLevel
from schemas.weather import WeatherInput


def detect_flood(
    weather: WeatherInput,
) -> HazardResult | None:
    """
    Detect a possible flood-related hazard.

    Parameters
    ----------
    weather:
        Validated weather observation or forecast.

    Returns
    -------
    HazardResult | None
        A standardized flood hazard when available rainfall
        information indicates elevated flood potential.

        Returns None when there is insufficient rainfall
        evidence.

    Screening rules
    ---------------
    Rainfall:

        >= 65 mm -> strong flood signal
        >= 35 mm -> moderate flood signal

    Precipitation probability:

        >= 80% -> supporting signal
        >= 60% -> weaker supporting signal

    A flood hazard requires either:

        1. Very heavy rainfall, or
        2. Heavy rainfall combined with high precipitation
           probability.
    """

    # --------------------------------------------------------------
    # Required rainfall input
    # --------------------------------------------------------------

    if weather.rainfall is None:
        return None

    rainfall = weather.rainfall

    # --------------------------------------------------------------
    # Precipitation probability
    # --------------------------------------------------------------

    precipitation_probability = (
        weather.precipitation_probability
    )

    # --------------------------------------------------------------
    # Determine flood signal
    # --------------------------------------------------------------

    strong_rainfall = rainfall >= 65.0
    moderate_rainfall = rainfall >= 35.0

    high_precipitation_probability = (
        precipitation_probability is not None
        and precipitation_probability >= 80.0
    )

    moderate_precipitation_probability = (
        precipitation_probability is not None
        and precipitation_probability >= 60.0
    )

    # --------------------------------------------------------------
    # Detection rule
    # --------------------------------------------------------------

    detected = (
        strong_rainfall
        or (
            moderate_rainfall
            and high_precipitation_probability
        )
    )

    if not detected:
        return None

    # --------------------------------------------------------------
    # Calculate flood screening score
    # --------------------------------------------------------------

    score = 0.0

    # Rainfall contribution
    if rainfall >= 150:
        score += 90
    elif rainfall >= 100:
        score += 75
    elif rainfall >= 65:
        score += 60
    elif rainfall >= 35:
        score += 45

    # Precipitation probability contribution
    if precipitation_probability is not None:
        if precipitation_probability >= 80:
            score += 20
        elif precipitation_probability >= 60:
            score += 10

    score = min(score, 100.0)

    # --------------------------------------------------------------
    # Determine severity
    # --------------------------------------------------------------

    if score >= 75:
        severity = RiskLevel.SEVERE
    elif score >= 50:
        severity = RiskLevel.HIGH
    else:
        severity = RiskLevel.MODERATE

    # --------------------------------------------------------------
    # Determine confidence
    # --------------------------------------------------------------

    if precipitation_probability is not None:
        confidence = 0.9
    else:
        confidence = 0.7

    # --------------------------------------------------------------
    # Build explanation
    # --------------------------------------------------------------

    signals = [
        f"rainfall of {rainfall:.1f} mm"
    ]

    if precipitation_probability is not None:
        signals.append(
            f"precipitation probability of "
            f"{precipitation_probability:.1f}%"
        )

    reason = (
        "Flood screening detected "
        + " combined with ".join(signals)
        + ", indicating elevated flood potential."
    )

    # --------------------------------------------------------------
    # Return standardized hazard result
    # --------------------------------------------------------------

    return HazardResult(
        hazard_type=HazardType.FLOOD,
        severity=severity,
        score=round(score, 2),
        confidence=confidence,
        reason=reason,
        location_name=weather.location_name,
        timestamp=weather.timestamp,
    )