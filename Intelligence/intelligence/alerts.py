"""
WeatherGPT - Member 3
Alert Intelligence Engine

Converts detected HazardResult objects into standardized
AlertResult objects for downstream applications.
"""

from __future__ import annotations

from datetime import timedelta

from schemas.alert import AlertResult, AlertStatus
from schemas.hazard import HazardResult, HazardType


def generate_alert(
    hazard: HazardResult,
) -> AlertResult:
    """
    Convert a single detected hazard into a standardized alert.

    The alert title, description, recommended action, and
    validity period depend on the detected hazard type.
    """

    location_name = (
        hazard.location_name
        if hazard.location_name
        else "Unknown Location"
    )

    if hazard.hazard_type == HazardType.HEAVY_RAINFALL:
        title = "Heavy Rainfall Warning"
        description = (
            "Heavy rainfall conditions have been detected "
            "with potential waterlogging and flooding impacts."
        )
        recommended_action = (
            "Avoid unnecessary travel and monitor official "
            "weather and emergency warnings."
        )
        validity_hours = 12

    elif hazard.hazard_type == HazardType.FLOOD:
        title = "Flood Risk Warning"
        description = (
            "Weather conditions indicate elevated flood "
            "potential in the affected area."
        )
        recommended_action = (
            "Avoid flooded areas, do not attempt to cross "
            "flooded roads, and move to safer locations "
            "if conditions worsen."
        )
        validity_hours = 12

    elif hazard.hazard_type == HazardType.HEATWAVE:
        title = "Heatwave Warning"
        description = (
            "High temperatures indicate increased heat-stress "
            "potential in the affected area."
        )
        recommended_action = (
            "Avoid prolonged outdoor exposure, stay hydrated, "
            "and follow local heat-safety guidance."
        )
        validity_hours = 12

    elif hazard.hazard_type == HazardType.CYCLONE:
        title = "Cyclone Warning"
        description = (
            "Weather conditions indicate potential cyclone-related "
            "hazards in the affected area."
        )
        recommended_action = (
            "Move to a safe location and follow official "
            "emergency instructions."
        )
        validity_hours = 24

    elif hazard.hazard_type == HazardType.EXTREME_WIND:
        title = "Extreme Wind Warning"
        description = (
            "Strong winds may create significant safety and "
            "operational risks in the affected area."
        )
        recommended_action = (
            "Secure loose objects, avoid unnecessary travel, "
            "and follow official warnings."
        )
        validity_hours = 12

    elif hazard.hazard_type == HazardType.EXTREME_WEATHER:
        title = "Extreme Weather Warning"
        description = (
            "Multiple hazardous weather conditions have been "
            "detected in the affected area."
        )
        recommended_action = (
            "Avoid unnecessary travel and follow official "
            "emergency and weather warnings."
        )
        validity_hours = 24

    else:
        title = "Weather Hazard Warning"
        description = hazard.reason
        recommended_action = (
            "Monitor weather conditions and follow official guidance."
        )
        validity_hours = 12

    title = f"{hazard.severity.value.title()} {title}"

    return AlertResult(
        alert_type=hazard.hazard_type,
        severity=hazard.severity,
        status=AlertStatus.ACTIVE,
        title=title,
        description=description,
        location_name=location_name,
        issued_at=hazard.timestamp,
        valid_from=hazard.timestamp,
        valid_until=hazard.timestamp + timedelta(hours=validity_hours),
        recommended_action=recommended_action,
        source="WeatherGPT Intelligence Engine",
    )


def generate_alerts(
    hazards: list[HazardResult],
) -> list[AlertResult]:
    """
    Generate alerts for all detected hazards.

    Parameters
    ----------
    hazards:
        List of standardized hazard results.

    Returns
    -------
    list[AlertResult]
        One alert for each detected hazard.
    """

    return [
        generate_alert(hazard)
        for hazard in hazards
    ]