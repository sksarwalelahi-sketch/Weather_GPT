"""
WeatherGPT - Risk Scoring Engine

Member 2: AI / LLM / Weather Intelligence

Calculates an overall weather risk score from
detected alerts and weather conditions.
"""

from typing import Dict, List, Any


# =========================================================
# SEVERITY WEIGHTS
# =========================================================

SEVERITY_WEIGHTS = {
    "LOW": 10,
    "MODERATE": 25,
    "HIGH": 40,
    "SEVERE": 60,
}


# =========================================================
# ALERT TYPE WEIGHTS
# =========================================================

ALERT_TYPE_WEIGHTS = {
    "heavy_rain": 20,
    "thunderstorm": 20,
    "strong_wind": 15,
    "extreme_heat": 20,
    "heat": 10,
    "extreme_cold": 20,
    "cold": 10,
    "low_visibility": 20,
}


# =========================================================
# SAFE NUMBER CONVERSION
# =========================================================

def to_float(value):
    """Convert value to float safely."""

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# =========================================================
# RISK LEVEL
# =========================================================

def get_risk_level(score: int) -> str:
    """Convert numeric score into risk category."""

    if score >= 80:
        return "SEVERE"

    if score >= 60:
        return "HIGH"

    if score >= 30:
        return "MODERATE"

    return "LOW"


# =========================================================
# WEATHER FACTOR ANALYSIS
# =========================================================

def calculate_weather_factor_score(
    weather_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate additional risk from raw weather values.
    """

    score = 0
    factors = []

    if not isinstance(weather_data, dict):
        return {
            "score": 0,
            "factors": [],
        }

    # -----------------------------------------------------
    # Rainfall
    # -----------------------------------------------------

    rainfall = weather_data.get("rainfall_mm")

    if rainfall is None:
        rainfall = weather_data.get("precipitation_mm")

    rainfall = to_float(rainfall)

    if rainfall is not None:

        if rainfall >= 50:
            score += 30
            factors.append("Extreme rainfall")

        elif rainfall >= 20:
            score += 25
            factors.append("Very heavy rainfall")

        elif rainfall >= 10:
            score += 15
            factors.append("Heavy rainfall")

        elif rainfall >= 5:
            score += 5
            factors.append("Moderate rainfall")

    # -----------------------------------------------------
    # Rain probability
    # -----------------------------------------------------

    rain_probability = to_float(
        weather_data.get("rain_probability")
    )

    if rain_probability is not None:

        if rain_probability >= 90:
            score += 10
            factors.append("Very high rain probability")

        elif rain_probability >= 70:
            score += 5
            factors.append("High rain probability")

    # -----------------------------------------------------
    # Wind
    # -----------------------------------------------------

    wind_speed = to_float(
        weather_data.get("wind_speed_kmh")
    )

    if wind_speed is not None:

        if wind_speed >= 60:
            score += 25
            factors.append("Very strong wind")

        elif wind_speed >= 40:
            score += 15
            factors.append("Strong wind")

        elif wind_speed >= 30:
            score += 5
            factors.append("Moderately strong wind")

    # -----------------------------------------------------
    # Temperature
    # -----------------------------------------------------

    temperature = to_float(
        weather_data.get("temperature_c")
    )

    temperature_max = to_float(
        weather_data.get("temperature_max_c")
    )

    temperature_min = to_float(
        weather_data.get("temperature_min_c")
    )

    # Use forecast maximum when available
    max_temp = temperature_max

    if max_temp is None:
        max_temp = temperature

    if max_temp is not None:

        if max_temp >= 45:
            score += 25
            factors.append("Extreme heat")

        elif max_temp >= 40:
            score += 15
            factors.append("High heat")

        elif max_temp >= 35:
            score += 5
            factors.append("Hot weather")

    # -----------------------------------------------------
    # Cold
    # -----------------------------------------------------

    min_temp = temperature_min

    if min_temp is None:
        min_temp = temperature

    if min_temp is not None:

        if min_temp <= 0:
            score += 25
            factors.append("Extreme cold")

        elif min_temp <= 5:
            score += 15
            factors.append("Very cold weather")

        elif min_temp <= 10:
            score += 5
            factors.append("Cold weather")

    # -----------------------------------------------------
    # Condition
    # -----------------------------------------------------

    condition = str(
        weather_data.get("condition", "")
    ).lower()

    if "thunderstorm" in condition:
        score += 20
        factors.append("Thunderstorm")

    elif "lightning" in condition:
        score += 20
        factors.append("Lightning")

    # -----------------------------------------------------
    # Return
    # -----------------------------------------------------

    return {
        "score": score,
        "factors": factors,
    }


# =========================================================
# ALERT SCORE
# =========================================================

def calculate_alert_score(
    alert_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate risk contribution from detected alerts.
    """

    score = 0
    factors = []

    if not isinstance(alert_result, dict):
        return {
            "score": 0,
            "factors": [],
        }

    alerts = alert_result.get(
        "alerts",
        []
    )

    for alert in alerts:

        if not isinstance(alert, dict):
            continue

        alert_type = alert.get(
            "type"
        )

        severity = alert.get(
            "severity",
            "LOW"
        )

        # Alert-specific weight
        type_score = ALERT_TYPE_WEIGHTS.get(
            alert_type,
            10
        )

        # Severity multiplier
        severity_multiplier = {
            "LOW": 0.5,
            "MODERATE": 0.75,
            "HIGH": 1.0,
            "SEVERE": 1.25,
        }.get(
            severity,
            1.0
        )

        contribution = round(
            type_score * severity_multiplier
        )

        score += contribution

        factors.append({
            "type": alert_type,
            "severity": severity,
            "score": contribution,
        })

    return {
        "score": score,
        "factors": factors,
    }


# =========================================================
# MAIN RISK SCORER
# =========================================================

def calculate_risk(
    weather_data: Dict[str, Any],
    alert_result: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Calculate overall weather risk.

    Parameters
    ----------
    weather_data:
        Structured weather information.

    alert_result:
        Output from detect_alerts().
    """

    if alert_result is None:
        alert_result = {
            "alerts": []
        }

    # -----------------------------------------------------
    # Weather-based score
    # -----------------------------------------------------

    weather_result = calculate_weather_factor_score(
        weather_data
    )

    weather_score = weather_result["score"]

    weather_factors = weather_result["factors"]

    # -----------------------------------------------------
    # Alert-based score
    # -----------------------------------------------------

    alert_result_score = calculate_alert_score(
        alert_result
    )

    alert_score = alert_result_score["score"]

    alert_factors = alert_result_score["factors"]

    # -----------------------------------------------------
    # Combined score
    # -----------------------------------------------------

    raw_score = weather_score + alert_score

    # Maximum risk score = 100
    final_score = min(
        round(raw_score),
        100
    )

    # -----------------------------------------------------
    # Risk level
    # -----------------------------------------------------

    risk_level = get_risk_level(
        final_score
    )

    # -----------------------------------------------------
    # Combine factors
    # -----------------------------------------------------

    factors = []

    for factor in weather_factors:

        if factor not in factors:
            factors.append(factor)

    for factor in alert_factors:

        factor_name = factor.get("type")

        if factor_name:
            readable_name = (
                factor_name.replace(
                    "_",
                    " "
                ).title()
            )

            if readable_name not in factors:
                factors.append(
                    readable_name
                )

    # -----------------------------------------------------
    # Return
    # -----------------------------------------------------

    return {
        "status": "success",
        "score": final_score,
        "level": risk_level,
        "weather_score": weather_score,
        "alert_score": alert_score,
        "factors": factors,
        "alert_count": len(
            alert_result.get(
                "alerts",
                []
            )
        ),
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    from app.intelligence.alert_detector import (
        detect_alerts
    )

    print("=" * 60)
    print("WeatherGPT - Risk Scoring Engine")
    print("=" * 60)

    # -----------------------------------------------------
    # Dangerous sample weather
    # -----------------------------------------------------

    sample_weather = {

        "temperature_max_c": 43.5,

        "temperature_min_c": 26.0,

        "rain_probability": 90,

        "rainfall_mm": 25.0,

        "humidity": 85,

        "wind_speed_kmh": 48,

        "condition": "Thunderstorm",
    }

    # -----------------------------------------------------
    # Detect alerts first
    # -----------------------------------------------------

    alert_result = detect_alerts(
        sample_weather
    )

    # -----------------------------------------------------
    # Calculate risk
    # -----------------------------------------------------

    risk_result = calculate_risk(
        sample_weather,
        alert_result
    )

    # -----------------------------------------------------
    # Display
    # -----------------------------------------------------

    print("\nRISK ANALYSIS")
    print("-" * 60)

    print(
        "Risk Score:",
        risk_result["score"]
    )

    print(
        "Risk Level:",
        risk_result["level"]
    )

    print(
        "Weather Score:",
        risk_result["weather_score"]
    )

    print(
        "Alert Score:",
        risk_result["alert_score"]
    )

    print(
        "Alert Count:",
        risk_result["alert_count"]
    )

    print("\nRisk Factors:")

    for factor in risk_result["factors"]:
        print(
            f"- {factor}"
        )

    print("\nFull Result:")
    print(
        risk_result
    )