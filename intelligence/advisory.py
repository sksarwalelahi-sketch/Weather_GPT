"""
WeatherGPT - Member 3
Advisory Intelligence Engine

Converts detected weather hazards into structured
decision-support advisories.
"""

from __future__ import annotations

from datetime import timedelta

from schemas.advisory import (
    AdvisoryDomain,
    AdvisoryPriority,
    AdvisoryResult,
)
from schemas.hazard import HazardResult, HazardType
from schemas.risk import RiskLevel


def _priority_from_risk(
    risk_level: RiskLevel,
) -> AdvisoryPriority:
    """Map weather risk severity to advisory priority."""

    mapping = {
        RiskLevel.LOW: AdvisoryPriority.LOW,
        RiskLevel.MODERATE: AdvisoryPriority.MEDIUM,
        RiskLevel.HIGH: AdvisoryPriority.HIGH,
        RiskLevel.SEVERE: AdvisoryPriority.CRITICAL,
    }

    return mapping[risk_level]


def generate_advisory(
    hazard: HazardResult,
) -> AdvisoryResult:
    """
    Convert one HazardResult into an AdvisoryResult.
    """

    location_name = (
        hazard.location_name
        if hazard.location_name
        else "Unknown Location"
    )

    priority = _priority_from_risk(hazard.severity)

    if hazard.hazard_type == HazardType.HEAVY_RAINFALL:
        title = "Heavy Rainfall Advisory"

        message = (
            "Heavy rainfall may cause waterlogging, reduced "
            "visibility, and localized flooding."
        )

        actions = [
            "Avoid unnecessary travel during intense rainfall.",
            "Avoid waterlogged and flooded roads.",
            "Monitor official weather and emergency warnings.",
        ]

        valid_hours = 12

    elif hazard.hazard_type == HazardType.FLOOD:
        title = "Flood Risk Advisory"

        message = (
            "Current weather conditions indicate elevated "
            "flood potential in the affected area."
        )

        actions = [
            "Avoid flooded roads and low-lying areas.",
            "Do not attempt to cross flowing or flooded water.",
            "Move to a safer location if flooding worsens.",
            "Follow official emergency instructions.",
        ]

        valid_hours = 12

    elif hazard.hazard_type == HazardType.HEATWAVE:
        title = "Heatwave Advisory"

        message = (
            "High temperatures may cause significant heat "
            "stress and health risks."
        )

        actions = [
            "Avoid prolonged outdoor exposure.",
            "Stay hydrated throughout the day.",
            "Prefer shaded or cool environments.",
            "Follow local heat-safety guidance.",
        ]

        valid_hours = 12

    elif hazard.hazard_type == HazardType.CYCLONE:
        title = "Cyclone Advisory"

        message = (
            "Weather conditions indicate potential cyclone-related "
            "risks including strong winds and heavy rainfall."
        )

        actions = [
            "Follow official cyclone warnings and instructions.",
            "Move to a safe location if evacuation is advised.",
            "Secure loose outdoor objects.",
            "Avoid coastal and exposed areas during severe conditions.",
        ]

        valid_hours = 24

    elif hazard.hazard_type == HazardType.EXTREME_WIND:
        title = "Extreme Wind Advisory"

        message = (
            "Strong winds may create safety risks and disrupt "
            "normal outdoor and transport activities."
        )

        actions = [
            "Secure loose objects and outdoor equipment.",
            "Avoid unnecessary travel during severe winds.",
            "Stay away from damaged structures and power lines.",
            "Follow official weather warnings.",
        ]

        valid_hours = 12

    elif hazard.hazard_type == HazardType.EXTREME_WEATHER:
        title = "Extreme Weather Advisory"

        message = (
            "Multiple hazardous weather conditions may create "
            "significant safety risks."
        )

        actions = [
            "Avoid unnecessary travel.",
            "Monitor official weather warnings.",
            "Follow emergency instructions.",
        ]

        valid_hours = 24

    else:
        title = "Weather Hazard Advisory"

        message = hazard.reason

        actions = [
            "Monitor weather conditions.",
            "Follow official safety guidance.",
        ]

        valid_hours = 12

    return AdvisoryResult(
        domain=AdvisoryDomain.GENERAL,
        priority=priority,
        risk_level=hazard.severity,
        title=title,
        message=message,
        actions=actions,
        location_name=location_name,
        issued_at=hazard.timestamp,
        valid_until=hazard.timestamp + timedelta(hours=valid_hours),
        source="WeatherGPT Intelligence Engine",
    )


def generate_advisories(
    hazards: list[HazardResult],
) -> list[AdvisoryResult]:
    """
    Generate advisories for all detected hazards.
    """

    return [
        generate_advisory(hazard)
        for hazard in hazards
    ]