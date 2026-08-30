"""
WeatherGPT - Member 3
Hazard Intelligence Orchestrator

This module coordinates the individual hazard detection
engines and returns standardized HazardResult objects.

The individual hazard detectors remain independent:

    heatwave.py
    cyclone.py
    flood.py
    etc.

This module is responsible only for orchestration.
"""

from __future__ import annotations

from schemas.hazard import HazardResult
from schemas.weather import WeatherInput


def detect_hazards(
    weather: WeatherInput,
) -> list[HazardResult]:
    """
    Detect weather hazards from a WeatherInput object.

    Parameters
    ----------
    weather:
        Validated weather observation.

    Returns
    -------
    list[HazardResult]
        Detected hazards.

    Notes
    -----
    Individual hazard detectors will be connected to this
    orchestrator incrementally.

    At this stage, the orchestrator intentionally returns
    an empty list until the first hazard detector is added.
    """

    hazards: list[HazardResult] = []

    return hazards