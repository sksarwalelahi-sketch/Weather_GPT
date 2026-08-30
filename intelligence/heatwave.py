"""
WeatherGPT - Member 3
Heatwave Hazard Detector

Converts temperature risk information into a standardized
Heatwave HazardResult.

The detector reuses the existing heat-risk engine instead
of duplicating temperature scoring logic.
"""

from __future__ import annotations

from schemas.hazard import HazardResult, HazardType
from schemas.risk import RiskLevel
from schemas.weather import WeatherInput

from intelligence.risk import calculate_heat_risk


def detect_heatwave(
    weather: WeatherInput,
) -> HazardResult | None:
    """
    Detect a heatwave hazard from a WeatherInput.

    Parameters
    ----------
    weather:
        Validated weather observation.

    Returns
    -------
    HazardResult | None
        A standardized heatwave hazard when temperature
        reaches the HIGH risk category or above.

        Returns None when temperature is unavailable or
        below the heatwave hazard threshold.

    Development rule:

        HIGH   -> Heatwave hazard
        SEVERE -> Heatwave hazard

        LOW / MODERATE -> No heatwave hazard
    """

    if weather.temperature is None:
        return None

    risk = calculate_heat_risk(
        weather.temperature
    )

    if risk.level not in {
        RiskLevel.HIGH,
        RiskLevel.SEVERE,
    }:
        return None

    if risk.level == RiskLevel.SEVERE:
        reason = (
            f"Temperature of {weather.temperature:.1f}°C "
            "indicates severe heat conditions with "
            "potential for significant heat stress."
        )
    else:
        reason = (
            f"Temperature of {weather.temperature:.1f}°C "
            "indicates high heat stress potential."
        )

    return HazardResult(
        hazard_type=HazardType.HEATWAVE,
        severity=risk.level,
        score=risk.score,
        confidence=1.0,
        reason=reason,
        location_name=weather.location_name,
        timestamp=weather.timestamp,
    )