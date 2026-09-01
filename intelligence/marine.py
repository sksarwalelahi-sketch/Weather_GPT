"""
WeatherGPT - Member 3
Marine Advisory Engine
"""

from __future__ import annotations

from schemas.advisory import (
    AdvisoryDomain,
    AdvisoryPriority,
    AdvisoryResult,
)
from schemas.hazard import HazardResult, HazardType
from schemas.risk import RiskLevel


def generate_marine_advisory(
    hazard: HazardResult,
) -> AdvisoryResult | None:
    """Generate a marine and coastal advisory."""

    location_name = (
        hazard.location_name
        if hazard.location_name
        else "Unknown Location"
    )

    if hazard.hazard_type == HazardType.EXTREME_WIND:
        title = "Marine Extreme Wind Advisory"
        message = (
            "Strong winds may create dangerous conditions for "
            "vessels and coastal activities."
        )
        actions = [
            "Avoid unnecessary marine operations.",
            "Secure vessels and marine equipment.",
            "Monitor official marine weather warnings.",
        ]

    elif hazard.hazard_type == HazardType.CYCLONE:
        title = "Marine Cyclone Advisory"
        message = (
            "Cyclone conditions may create dangerous marine "
            "and coastal conditions."
        )
        actions = [
            "Avoid unnecessary marine operations.",
            "Move vessels to safe harbor when advised.",
            "Follow official cyclone and coastal warnings.",
        ]

    elif hazard.hazard_type == HazardType.HEAVY_RAINFALL:
        title = "Marine Heavy Rainfall Advisory"
        message = (
            "Heavy rainfall may reduce visibility and create "
            "difficult operating conditions for vessels."
        )
        actions = [
            "Monitor visibility and weather conditions.",
            "Use appropriate navigation precautions.",
            "Avoid unnecessary marine operations during severe rainfall.",
        ]

    elif hazard.hazard_type == HazardType.FLOOD:
        title = "Coastal Flood Risk Advisory"
        message = (
            "Flooding may affect coastal areas, ports, and "
            "marine infrastructure."
        )
        actions = [
            "Monitor coastal flood warnings.",
            "Protect marine equipment and infrastructure.",
            "Avoid operating in affected coastal areas.",
        ]

    else:
        return None

    priority_map = {
        RiskLevel.LOW: AdvisoryPriority.LOW,
        RiskLevel.MODERATE: AdvisoryPriority.MEDIUM,
        RiskLevel.HIGH: AdvisoryPriority.HIGH,
        RiskLevel.SEVERE: AdvisoryPriority.CRITICAL,
    }

    return AdvisoryResult(
        domain=AdvisoryDomain.MARINE,
        priority=priority_map[hazard.severity],
        risk_level=hazard.severity,
        title=title,
        message=message,
        actions=actions,
        location_name=location_name,
        issued_at=hazard.timestamp,
        source="WeatherGPT Intelligence Engine",
    )


def generate_marine_advisories(
    hazards: list[HazardResult],
) -> list[AdvisoryResult]:
    """Generate marine advisories for supported hazards."""

    advisories = []

    for hazard in hazards:
        advisory = generate_marine_advisory(hazard)

        if advisory is not None:
            advisories.append(advisory)

    return advisories