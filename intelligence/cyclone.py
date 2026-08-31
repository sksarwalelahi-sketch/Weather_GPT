"""
WeatherGPT - Member 3
Cyclone Hazard Detector

Provides a first-pass, rule-based cyclone hazard detector
using the weather signals currently available in WeatherInput.

The detector combines:
    - wind speed
    - wind gust
    - atmospheric pressure
    - rainfall
    - humidity

This is an intelligence-layer screening detector. It is not
intended to replace an official cyclone warning or forecast.
"""

from __future__ import annotations

from schemas.hazard import HazardResult, HazardType
from schemas.risk import RiskLevel
from schemas.weather import WeatherInput


def detect_cyclone(
    weather: WeatherInput,
) -> HazardResult | None:
    """
    Detect a possible cyclone-related hazard.

    The detector uses available weather observations to build
    a rule-based cyclone signal score.

    Returns
    -------
    HazardResult | None
        A cyclone hazard when enough supporting signals exist.

        Returns None when there is insufficient evidence.

    Signal rules
    ------------
    Wind speed:
        >= 60 km/h  -> strong cyclone signal
        >= 40 km/h  -> moderate cyclone signal

    Wind gust:
        >= 90 km/h  -> strong cyclone signal
        >= 60 km/h  -> moderate cyclone signal

    Pressure:
        <= 990 hPa  -> strong cyclone signal
        <= 1000 hPa -> moderate cyclone signal

    Rainfall:
        >= 65 mm -> supporting cyclone signal
        >= 35 mm -> weaker supporting signal

    Humidity:
        >= 80% -> supporting atmospheric signal

    A cyclone hazard requires strong wind evidence plus
    at least one additional supporting signal.
    """

    signals: list[str] = []
    strong_wind = False

    # --------------------------------------------------------------
    # Wind speed
    # --------------------------------------------------------------

    if weather.wind_speed is not None:

        if weather.wind_speed >= 60:
            strong_wind = True
            signals.append(
                f"wind speed of {weather.wind_speed:.1f} km/h"
            )

        elif weather.wind_speed >= 40:
            signals.append(
                f"wind speed of {weather.wind_speed:.1f} km/h"
            )

    # --------------------------------------------------------------
    # Wind gust
    # --------------------------------------------------------------

    if weather.wind_gust is not None:

        if weather.wind_gust >= 90:
            strong_wind = True
            signals.append(
                f"wind gusts of {weather.wind_gust:.1f} km/h"
            )

        elif weather.wind_gust >= 60:
            signals.append(
                f"wind gusts of {weather.wind_gust:.1f} km/h"
            )

    # --------------------------------------------------------------
    # Atmospheric pressure
    # --------------------------------------------------------------

    pressure_support = False

    if weather.pressure is not None:

        if weather.pressure <= 990:
            pressure_support = True
            signals.append(
                f"low atmospheric pressure of "
                f"{weather.pressure:.1f} hPa"
            )

        elif weather.pressure <= 1000:
            signals.append(
                f"reduced atmospheric pressure of "
                f"{weather.pressure:.1f} hPa"
            )

    # --------------------------------------------------------------
    # Rainfall
    # --------------------------------------------------------------

    rainfall_support = False

    if weather.rainfall is not None:

        if weather.rainfall >= 65:
            rainfall_support = True
            signals.append(
                f"heavy rainfall of {weather.rainfall:.1f} mm"
            )

        elif weather.rainfall >= 35:
            signals.append(
                f"rainfall of {weather.rainfall:.1f} mm"
            )

    # --------------------------------------------------------------
    # Humidity
    # --------------------------------------------------------------

    humidity_support = False

    if weather.humidity is not None:

        if weather.humidity >= 80:
            humidity_support = True
            signals.append(
                f"high humidity of {weather.humidity:.1f}%"
            )

    # --------------------------------------------------------------
    # Detection requirement
    # --------------------------------------------------------------

    supporting_signals = sum(
        [
            pressure_support,
            rainfall_support,
            humidity_support,
        ]
    )

    if not strong_wind:
        return None

    if supporting_signals == 0:
        return None

    # --------------------------------------------------------------
    # Hazard score
    # --------------------------------------------------------------

    score = 50.0

    if weather.wind_speed is not None:
        if weather.wind_speed >= 90:
            score += 20
        elif weather.wind_speed >= 60:
            score += 15
        elif weather.wind_speed >= 40:
            score += 10

    if weather.wind_gust is not None:
        if weather.wind_gust >= 120:
            score += 15
        elif weather.wind_gust >= 90:
            score += 10
        elif weather.wind_gust >= 60:
            score += 5

    if weather.pressure is not None:
        if weather.pressure <= 990:
            score += 10
        elif weather.pressure <= 1000:
            score += 5

    if weather.rainfall is not None:
        if weather.rainfall >= 65:
            score += 10
        elif weather.rainfall >= 35:
            score += 5

    if weather.humidity is not None and weather.humidity >= 80:
        score += 5

    score = min(score, 100.0)

    # --------------------------------------------------------------
    # Severity
    # --------------------------------------------------------------

    if score >= 75:
        severity = RiskLevel.SEVERE
    elif score >= 50:
        severity = RiskLevel.HIGH
    else:
        severity = RiskLevel.MODERATE

    # --------------------------------------------------------------
    # Confidence
    # --------------------------------------------------------------

    available_signals = sum(
        value is not None
        for value in [
            weather.wind_speed,
            weather.wind_gust,
            weather.pressure,
            weather.rainfall,
            weather.humidity,
        ]
    )

    confidence = min(
        1.0,
        0.5 + (available_signals * 0.1)
    )

    # --------------------------------------------------------------
    # Explanation
    # --------------------------------------------------------------

    reason = (
        "Cyclone screening detected a combination of "
        + ", ".join(signals)
        + "."
    )

    return HazardResult(
        hazard_type=HazardType.CYCLONE,
        severity=severity,
        score=round(score, 2),
        confidence=round(confidence, 2),
        reason=reason,
        location_name=weather.location_name,
        timestamp=weather.timestamp,
    )
