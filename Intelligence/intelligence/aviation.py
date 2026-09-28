"""
WeatherGPT - Member 3
Aviation Advisory Engine
"""

from __future__ import annotations

from schemas.advisory import (
    AdvisoryDomain,
    AdvisoryPriority,
    AdvisoryResult,
)
from schemas.hazard import HazardResult, HazardType
from schemas.risk import RiskLevel


def generate_aviation_advisory(
    hazard: HazardResult,
) -> AdvisoryResult | None:
    """Generate an aviation-specific advisory."""

    location_name = (
        hazard.location_name
        if hazard.location_name
        else "Unknown Location"
    )

    if hazard.hazard_type == HazardType.EXTREME_WIND:
        title = "Aviation Extreme Wind Advisory"
        message = (
            "Strong winds may affect aircraft operations, "
            "ground handling, and airport safety."
        )
        actions = [
            "Review current wind and gust conditions.",
            "Exercise caution during aircraft ground operations.",
            "Monitor airport operational restrictions.",
        ]

    elif hazard.hazard_type == HazardType.HEAVY_RAINFALL:
        title = "Aviation Heavy Rainfall Advisory"
        message = (
            "Heavy rainfall may reduce visibility and affect "
            "airport and flight operations."
        )
        actions = [
            "Monitor visibility and runway conditions.",
            "Review operational weather updates.",
            "Expect possible delays or operational restrictions.",
        ]

    elif hazard.hazard_type == HazardType.CYCLONE:
        title = "Aviation Cyclone Advisory"
        message = (
            "Cyclone conditions may significantly disrupt "
            "flight operations and airport activities."
        )
        actions = [
            "Monitor official aviation weather warnings.",
            "Review flight routing and operational restrictions.",
            "Secure airport ground equipment where required.",
        ]

    elif hazard.hazard_type == HazardType.FLOOD:
        title = "Aviation Flood Risk Advisory"
        message = (
            "Flooding may affect airport access, ground operations, "
            "and airport infrastructure."
        )
        actions = [
            "Monitor airport access and infrastructure conditions.",
            "Review local flood warnings.",
            "Prepare for possible operational disruption.",
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
        domain=AdvisoryDomain.AVIATION,
        priority=priority_map[hazard.severity],
        risk_level=hazard.severity,
        title=title,
        message=message,
        actions=actions,
        location_name=location_name,
        issued_at=hazard.timestamp,
        source="WeatherGPT Intelligence Engine",
    )


def generate_aviation_advisories(
    hazards: list[HazardResult],
) -> list[AdvisoryResult]:
    """Generate aviation advisories for supported hazards."""

    advisories = []

    for hazard in hazards:
        advisory = generate_aviation_advisory(hazard)

        if advisory is not None:
            advisories.append(advisory)

    return advisories