"""
WeatherGPT - Member 3
Heavy Rainfall Hazard Detector

Converts rainfall risk information into a standardized
Heavy Rainfall HazardResult.

The detector reuses the existing rainfall risk engine
instead of duplicating rainfall scoring logic.
"""

from __future__ import annotations

from schemas.hazard import HazardResult, HazardType
from schemas.risk import RiskLevel
from schemas.weather import WeatherInput

from intelligence.risk import calculate_rainfall_risk


def detect_heavy_rainfall(
    weather: WeatherInput,
) -> HazardResult | None:
    """
    Detect a heavy-rainfall hazard from a WeatherInput.

    Parameters
    ----------
    weather:
        Validated weather observation.

    Returns
    -------
    HazardResult | None
        A standardized heavy-rainfall hazard when rainfall
        reaches the HIGH risk category or above.

        Returns None when rainfall is unavailable or below
        the heavy-rainfall hazard threshold.

    Notes
    -----
    This first version uses the existing rainfall risk engine
    as the source of severity and score.

    Development rule:

        HIGH   -> Heavy Rainfall hazard
        SEVERE -> Heavy Rainfall hazard

        LOW / MODERATE -> No heavy-rainfall hazard
    """

    if weather.rainfall is None:
        return None

    risk = calculate_rainfall_risk(
        weather.rainfall
    )

    if risk.level not in {
        RiskLevel.HIGH,
        RiskLevel.SEVERE,
    }:
        return None

    if risk.level == RiskLevel.SEVERE:
        reason = (
            f"Rainfall of {weather.rainfall:.1f} mm indicates "
            "very heavy rainfall conditions with elevated "
            "waterlogging and flooding potential."
        )
    else:
        reason = (
            f"Rainfall of {weather.rainfall:.1f} mm indicates "
            "heavy rainfall conditions with potential "
            "waterlogging and localized flooding impacts."
        )

    return HazardResult(
        hazard_type=HazardType.HEAVY_RAINFALL,
        severity=risk.level,
        score=risk.score,
        confidence=1.0,
        reason=reason,
        location_name=weather.location_name,
        timestamp=weather.timestamp,
    )