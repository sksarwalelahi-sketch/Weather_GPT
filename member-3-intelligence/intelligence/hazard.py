"""
WeatherGPT - Member 3
Hazard Intelligence Orchestrator

Coordinates all available hazard detection engines
and returns standardized HazardResult objects.
"""

from __future__ import annotations

from schemas.hazard import HazardResult
from schemas.weather import WeatherInput

from intelligence.cyclone import detect_cyclone
from intelligence.extreme_wind import detect_extreme_wind
from intelligence.flood import detect_flood
from intelligence.heatwave import detect_heatwave
from intelligence.heavy_rain import detect_heavy_rainfall


def detect_hazards(
    weather: WeatherInput,
) -> list[HazardResult]:
    """
    Run all available hazard detectors for a weather input.

    Each detector is independent. A detector may return
    a HazardResult when a hazard is detected or None when
    conditions do not meet its detection criteria.
    """

    hazards: list[HazardResult] = []

    detectors = (
        detect_heavy_rainfall,
        detect_heatwave,
        detect_cyclone,
        detect_flood,
        detect_extreme_wind,
    )

    for detector in detectors:
        result = detector(weather)

        if result is not None:
            hazards.append(result)

    return hazards