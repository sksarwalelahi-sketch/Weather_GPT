"""
WeatherGPT - Member 3
Extreme Wind Hazard Detector

Converts wind risk information into a standardized
Extreme Wind HazardResult.

The detector reuses the existing wind risk engine
instead of duplicating wind scoring logic.
"""

from __future__ import annotations

from schemas.hazard import HazardResult, HazardType
from schemas.risk import RiskLevel
from schemas.weather import WeatherInput

from intelligence.risk import calculate_wind_risk


def detect_extreme_wind(
    weather: WeatherInput,
) -> HazardResult | None:
    """
    Detect an extreme-wind hazard from a WeatherInput.

    A hazard is generated when the calculated wind risk
    reaches HIGH or SEVERE.

    Wind gusts are also considered when they are higher
    than the reported sustained wind speed.
    """

    if weather.wind_speed is None and weather.wind_gust is None:
        return None

    # Use the strongest available wind measurement.
    wind_value = max(
        value
        for value in (
            weather.wind_speed,
            weather.wind_gust,
        )
        if value is not None
    )

    risk = calculate_wind_risk(wind_value)

    if risk.level not in {
        RiskLevel.HIGH,
        RiskLevel.SEVERE,
    }:
        return None

    if weather.wind_gust is not None and (
        weather.wind_speed is None
        or weather.wind_gust > weather.wind_speed
    ):
        wind_description = (
            f"wind gust of {weather.wind_gust:.1f} km/h"
        )
    else:
        wind_description = (
            f"wind speed of {wind_value:.1f} km/h"
        )

    if risk.level == RiskLevel.SEVERE:
        reason = (
            f"{wind_description} indicates severe wind "
            "conditions with increased safety and "
            "operational risks."
        )
    else:
        reason = (
            f"{wind_description} indicates strong wind "
            "conditions with potential safety and "
            "operational impacts."
        )

    return HazardResult(
        hazard_type=HazardType.EXTREME_WIND,
        severity=risk.level,
        score=risk.score,
        confidence=1.0,
        reason=reason,
        location_name=weather.location_name,
        timestamp=weather.timestamp,
    )