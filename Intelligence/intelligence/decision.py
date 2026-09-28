"""
WeatherGPT - Member 3
Final Decision Engine

Unified orchestration layer for the Weather Intelligence system.

This engine takes weather observations and combines:
    1. Risk assessment
    2. Hazard detection
    3. Alert generation
    4. General advisories
    5. Domain-specific advisories
    6. Climate analysis (when historical values are supplied)

The engine does not generate raw weather data.
It converts weather intelligence into one unified decision result.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from schemas.advisory import AdvisoryDomain, AdvisoryPriority, AdvisoryResult
from schemas.risk import RiskLevel
from intelligence.advisory import generate_advisories
from intelligence.alerts import generate_alerts
from intelligence.agriculture import generate_agriculture_advisories
from intelligence.aviation import generate_aviation_advisories
from intelligence.climate import (
    analyze_humidity,
    analyze_rainfall,
    analyze_temperature,
    analyze_wind_speed,
)
from intelligence.flood import detect_flood
from intelligence.cyclone import detect_cyclone
from intelligence.extreme_wind import detect_extreme_wind
from intelligence.hazard import detect_hazards
from intelligence.heavy_rain import detect_heavy_rainfall
from intelligence.heatwave import detect_heatwave
from intelligence.marine import generate_marine_advisories
from intelligence.risk import assess_weather_risk

from schemas.intelligence import WeatherIntelligenceResult
from schemas.weather import WeatherInput


def _generate_domain_advisories(hazards):
    """
    Generate domain-specific advisories from the detected hazards.

    Each domain engine returns its own advisory list.
    The results are combined into one list.
    """

    advisories = []

    advisories.extend(generate_agriculture_advisories(hazards))
    advisories.extend(generate_aviation_advisories(hazards))
    advisories.extend(generate_marine_advisories(hazards))

    return advisories


def _align_advisory_severity(
    advisories: list[AdvisoryResult],
    overall_level: RiskLevel,
) -> list[AdvisoryResult]:
    """Keep every advisory badge consistent with the unified risk level."""

    priority = {
        RiskLevel.LOW: AdvisoryPriority.LOW,
        RiskLevel.MODERATE: AdvisoryPriority.MEDIUM,
        RiskLevel.HIGH: AdvisoryPriority.HIGH,
        RiskLevel.SEVERE: AdvisoryPriority.CRITICAL,
    }[overall_level]
    for advisory in advisories:
        advisory.risk_level = overall_level
        advisory.priority = priority
    return advisories


def _generate_baseline_advisories(weather: WeatherInput) -> list[AdvisoryResult]:
    """Give live guidance for every supported decision-making domain."""
    location_name = weather.location_name or "Unknown Location"
    valid_until = weather.timestamp + timedelta(hours=3)

    if weather.rainfall is not None and weather.rainfall > 0:
        condition = "Rain is currently reported"
        travel_actions = [
            "Carry an umbrella or rain protection before going outside.",
            "Use headlights and reduce speed on wet roads.",
            "Avoid waterlogged roads, unsafe underpasses, and exposed electrical equipment.",
            "Recheck the latest radar and forecast before travelling.",
        ]
        agriculture_actions = [
            "Check field drainage and clear blocked channels before water accumulates.",
            "Protect harvested produce, seed, and fertiliser from getting wet.",
            "Postpone pesticide or fertiliser application when rain could wash it off.",
            "Avoid field work during lightning or intense rainfall.",
        ]
        marine_actions = [
            "Check visibility, wind, and the latest official marine bulletin before departure.",
            "Secure nets, fuel, electronics, and other loose equipment from water exposure.",
            "Use navigation lights and appropriate rain and spray protection when operating.",
            "Do not depart or continue operating if local authorities issue a restriction.",
        ]
        aviation_actions = [
            "Review current visibility, wind, runway condition, and airport operational updates.",
            "Allow additional time for taxiing, approach, and possible weather delays.",
            "Use the latest METAR, TAF, and operator briefing for flight decisions.",
            "Do not treat this advisory as a substitute for an official aviation briefing.",
        ]
    elif weather.temperature is not None and weather.temperature >= 32:
        condition = "Warm conditions are currently reported"
        travel_actions = [
            "Drink water regularly and take breaks in shade.",
            "Prefer lighter clothing and avoid strenuous outdoor work at peak heat.",
        ]
        agriculture_actions = [
            "Check crop water stress and irrigate according to crop and soil requirements.",
            "Move demanding field work to cooler morning or evening hours.",
            "Provide shade and drinking water for livestock.",
            "Monitor young plants and recently transplanted crops for heat stress.",
        ]
        marine_actions = [
            "Carry sufficient drinking water and sun protection for the crew.",
            "Check equipment and engine cooling before departure.",
            "Schedule strenuous deck work outside the hottest hours.",
        ]
        aviation_actions = [
            "Review density-altitude and aircraft performance implications where applicable.",
            "Plan hydration and heat protection for ramp and ground crews.",
            "Check airport heat-related operational notices.",
        ]
    elif weather.wind_speed is not None and weather.wind_speed >= 20:
        condition = "Noticeable winds are currently reported"
        travel_actions = [
            "Secure loose items on balconies, rooftops, and outdoor work areas.",
            "Take care near trees, temporary structures, and exposed roads.",
        ]
        agriculture_actions = [
            "Secure irrigation pipes, greenhouse covers, shade nets, and loose equipment.",
            "Inspect vulnerable trees, supports, and temporary farm structures.",
            "Protect livestock from exposed areas and postpone spraying.",
        ]
        marine_actions = [
            "Check wind speed, gusts, wave and official marine warnings before departure.",
            "Secure the vessel and fishing gear; seek safe harbour if conditions worsen.",
            "Do not operate a small vessel beyond its safe wind and sea-state limits.",
        ]
        aviation_actions = [
            "Review crosswind, gust, runway, and airport operational limits.",
            "Use the latest METAR, TAF, SIGMET, and operator briefing.",
            "Expect possible turbulence, routing changes, or ground-handling restrictions.",
        ]
    elif weather.visibility is not None and weather.visibility < 5:
        condition = "Visibility is reduced"
        travel_actions = ["Use appropriate lights, increase following distance, and allow extra travel time.", "Avoid unnecessary travel if visibility deteriorates further."]
        agriculture_actions = ["Delay machinery work until visibility improves.", "Use a buddy system for work near roads, water, or machinery."]
        marine_actions = ["Reduce speed, use navigation lights, maintain lookout, and follow restricted-visibility procedures.", "Check the latest marine bulletin before departure."]
        aviation_actions = ["Review current visibility, ceiling, approach minima, and airport operational updates.", "Use the latest METAR, TAF, and operator briefing."]
    else:
        condition = "No significant hazard threshold is active"
        travel_actions = ["Continue normal plans and check the forecast before time-sensitive travel.", "Keep local official warnings enabled."]
        agriculture_actions = ["Continue planned work while checking the short-term forecast.", "Maintain routine crop, soil, irrigation, and livestock monitoring."]
        marine_actions = ["Check the latest marine bulletin, wind, and sea-state information before departure.", "Maintain normal safety checks and communications."]
        aviation_actions = ["Use the latest METAR, TAF, NOTAM, and operator briefing for flight decisions.", "Continue normal aircraft, crew, and airport safety checks."]

    domain_guidance = [
        (
            AdvisoryDomain.AGRICULTURE,
            "Agriculture guidance",
            f"{condition} near {location_name}; field operations should account for the current conditions.",
            agriculture_actions,
        ),
        (
            AdvisoryDomain.URBAN,
            "Travel and urban guidance",
            f"{condition} in {location_name}; travel and outdoor movement may need extra planning.",
            travel_actions,
        ),
        (
            AdvisoryDomain.MARINE,
            "Fisheries and marine guidance",
            f"{condition} near {location_name}; fisheries and small-vessel activity should be reviewed before departure.",
            marine_actions,
        ),
        (
            AdvisoryDomain.AVIATION,
            "Flight and aviation guidance",
            f"{condition} near {location_name}; flight and airport operations should use the latest operational briefing.",
            aviation_actions,
        ),
    ]

    return [
        AdvisoryResult(
            domain=domain,
            priority=AdvisoryPriority.LOW,
            risk_level=RiskLevel.LOW,
            title=title,
            message=message,
            actions=actions,
            location_name=location_name,
            issued_at=weather.timestamp,
            valid_until=valid_until,
            source="WeatherGPT Intelligence Engine · live weather conditions",
        )
        for domain, title, message, actions in domain_guidance
    ]


def _build_climate_analysis(
    historical_values: dict | None,
    location_name: str,
):
    """
    Build climate analysis when historical metric data is available.

    Expected dictionary structure:

    {
        "temperature": {
            "values": [...],
            "baseline": 30.0,
            "period": "Last 30 days"
        },
        "rainfall": {
            "values": [...],
            "baseline": 5.0,
            "period": "Last 30 days"
        },
        "humidity": {
            "values": [...],
            "baseline": 60.0,
            "period": "Last 30 days"
        },
        "wind_speed": {
            "values": [...],
            "baseline": 15.0,
            "period": "Last 30 days"
        }
    }
    """

    if not historical_values:
        return []

    climate_results = []

    metric_functions = {
        "temperature": analyze_temperature,
        "rainfall": analyze_rainfall,
        "humidity": analyze_humidity,
        "wind_speed": analyze_wind_speed,
    }

    for metric_name, config in historical_values.items():
        if metric_name not in metric_functions:
            continue

        if not isinstance(config, dict):
            continue

        values = config.get("values")
        baseline = config.get("baseline")
        period = config.get("period", "Historical period")

        if not values or baseline is None:
            continue

        result = metric_functions[metric_name](
            values=values,
            baseline_value=baseline,
            period=period,
            location_name=location_name,
        )

        climate_results.append(result)

    return climate_results


def analyze_weather(
    weather: WeatherInput,
    historical_values: dict | None = None,
) -> WeatherIntelligenceResult:
    """
    Run the complete Member 3 intelligence pipeline for one
    weather observation.

    Parameters
    ----------
    weather:
        Current or forecast weather observation.

    historical_values:
        Optional historical weather data for climate analysis.

    Returns
    -------
    WeatherIntelligenceResult
        Unified intelligence output.
    """

    location_name = weather.location_name or "Unknown Location"

    # ---------------------------------------------------------
    # 1. Risk Assessment
    # ---------------------------------------------------------

    risk_assessment = assess_weather_risk(weather)

    # ---------------------------------------------------------
    # 2. Hazard Detection
    # ---------------------------------------------------------

    hazards = detect_hazards(weather)

    # ---------------------------------------------------------
    # 3. Alerts
    # ---------------------------------------------------------

    alerts = generate_alerts(hazards)

    # ---------------------------------------------------------
    # 4. General Advisories
    # ---------------------------------------------------------

    advisories = generate_advisories(hazards)
    advisories = _generate_baseline_advisories(weather) + advisories

    # ---------------------------------------------------------
    # 5. Domain-Specific Advisories
    # ---------------------------------------------------------

    advisories.extend(
        _generate_domain_advisories(hazards)
    )
    advisories = _align_advisory_severity(
        advisories,
        risk_assessment.overall_level,
    )

    # ---------------------------------------------------------
    # 6. Climate Analysis
    # ---------------------------------------------------------

    climate_analysis = _build_climate_analysis(
        historical_values=historical_values,
        location_name=location_name,
    )

    # ---------------------------------------------------------
    # 7. Unified Result
    # ---------------------------------------------------------

    return WeatherIntelligenceResult(
        location_name=location_name,
        generated_at=datetime.now(),
        risk_assessment=risk_assessment,
        hazards=hazards,
        alerts=alerts,
        advisories=advisories,
        climate_analysis=climate_analysis,
    )


def analyze_weather_batch(
    weather_points: Iterable[WeatherInput],
    historical_values: dict | None = None,
) -> list[WeatherIntelligenceResult]:
    """
    Run the decision engine for multiple weather observations.
    """

    observations = list(weather_points)

    if not observations:
        raise ValueError("At least one weather observation is required.")

    return [
        analyze_weather(
            weather=weather,
            historical_values=historical_values,
        )
        for weather in observations
    ]


def get_decision_summary(
    result: WeatherIntelligenceResult,
) -> dict:
    """
    Convert the unified intelligence result into a compact
    decision summary suitable for APIs, dashboards, or mobile UI.
    """

    return {
        "location": result.location_name,
        "risk_level": (
            result.risk_assessment.overall_level.value
            if result.risk_assessment
            else "LOW"
        ),
        "risk_score": (
            result.risk_assessment.overall_score
            if result.risk_assessment
            else 0.0
        ),
        "hazard_count": len(result.hazards),
        "alert_count": len(result.alerts),
        "advisory_count": len(result.advisories),
        "climate_analysis_count": len(result.climate_analysis),
        "generated_at": result.generated_at,
    }