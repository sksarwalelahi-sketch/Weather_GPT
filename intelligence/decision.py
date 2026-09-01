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
from datetime import datetime

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

    # ---------------------------------------------------------
    # 5. Domain-Specific Advisories
    # ---------------------------------------------------------

    advisories.extend(
        _generate_domain_advisories(hazards)
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