"""
WeatherGPT - Member 3
Agriculture Advisory Engine

Generates agriculture-specific decision-support advisories
from detected weather hazards.
"""

from __future__ import annotations

from schemas.advisory import (
    AdvisoryDomain,
    AdvisoryPriority,
    AdvisoryResult,
)
from schemas.hazard import HazardResult, HazardType
from schemas.risk import RiskLevel


def generate_agriculture_advisory(
    hazard: HazardResult,
) -> AdvisoryResult | None:
    """Generate an agriculture advisory for a supported hazard."""

    location_name = (
        hazard.location_name
        if hazard.location_name
        else "Unknown Location"
    )

    if hazard.hazard_type == HazardType.HEAVY_RAINFALL:
        title = "Agricultural Heavy Rainfall Advisory"
        message = (
            "Heavy rainfall may cause field waterlogging, "
            "soil erosion, and disruption to agricultural operations."
        )
        actions = [
            "Avoid unnecessary field operations during intense rainfall.",
            "Check drainage in cultivated fields.",
            "Protect harvested crops and stored agricultural produce.",
            "Monitor local rainfall and flood warnings.",
        ]

    elif hazard.hazard_type == HazardType.FLOOD:
        title = "Agricultural Flood Risk Advisory"
        message = (
            "Flood conditions may damage crops, agricultural "
            "infrastructure, and stored produce."
        )
        actions = [
            "Move equipment and vulnerable materials to safer locations.",
            "Protect livestock from flooded and low-lying areas.",
            "Avoid agricultural operations in flooded fields.",
            "Follow local flood and emergency guidance.",
        ]

    elif hazard.hazard_type == HazardType.HEATWAVE:
        title = "Agricultural Heatwave Advisory"
        message = (
            "High temperatures may cause crop heat stress, "
            "increased water demand, and livestock stress."
        )
        actions = [
            "Increase monitoring of crop water requirements.",
            "Provide adequate drinking water for livestock.",
            "Avoid unnecessary field work during peak heat.",
            "Use available crop and livestock heat-protection measures.",
        ]

    elif hazard.hazard_type == HazardType.CYCLONE:
        title = "Agricultural Cyclone Advisory"
        message = (
            "Cyclone conditions may cause strong winds, heavy rainfall, "
            "flooding, and damage to crops and agricultural infrastructure."
        )
        actions = [
            "Secure agricultural equipment and loose structures.",
            "Move livestock to safer locations.",
            "Protect harvested crops and stored produce.",
            "Follow official cyclone and evacuation instructions.",
        ]

    elif hazard.hazard_type == HazardType.EXTREME_WIND:
        title = "Agricultural Extreme Wind Advisory"
        message = (
            "Strong winds may damage crops, farm structures, "
            "greenhouses, and agricultural equipment."
        )
        actions = [
            "Secure loose agricultural equipment.",
            "Inspect vulnerable farm structures.",
            "Protect livestock from exposed areas.",
            "Avoid unnecessary outdoor farm operations.",
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
        domain=AdvisoryDomain.AGRICULTURE,
        priority=priority_map[hazard.severity],
        risk_level=hazard.severity,
        title=title,
        message=message,
        actions=actions,
        location_name=location_name,
        issued_at=hazard.timestamp,
        source="WeatherGPT Intelligence Engine",
    )


def generate_agriculture_advisories(
    hazards: list[HazardResult],
) -> list[AdvisoryResult]:
    """Generate agriculture advisories for all supported hazards."""

    advisories = []

    for hazard in hazards:
        advisory = generate_agriculture_advisory(hazard)

        if advisory is not None:
            advisories.append(advisory)

    return advisories