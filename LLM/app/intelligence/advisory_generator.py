"""
WeatherGPT - Advisory Generator

Member 2: AI / LLM / Weather Intelligence

Converts detected weather alerts into actionable
user-friendly recommendations.
"""


# =========================================================
# ADVISORY DATABASE
# =========================================================

ADVISORY_RULES = {

    "heavy_rain": {
        "title": "Heavy Rain Advisory",
        "advice": [
            "Avoid unnecessary outdoor travel.",
            "Carry rain protection when going outside.",
            "Drive carefully because roads may become slippery or waterlogged.",
            "Avoid crossing flooded roads or flowing water.",
            "Keep important belongings and electronic devices protected from water.",
        ],
    },

    "thunderstorm": {
        "title": "Thunderstorm Advisory",
        "advice": [
            "Stay indoors during thunderstorms.",
            "Avoid open fields and exposed areas.",
            "Stay away from trees, electric poles, and isolated structures.",
            "Avoid using electrical appliances during severe lightning activity.",
            "Do not shelter under trees during lightning.",
        ],
    },

    "strong_wind": {
        "title": "Strong Wind Advisory",
        "advice": [
            "Avoid unnecessary outdoor activities.",
            "Stay away from trees, hoardings, and weak structures.",
            "Secure loose objects around homes and buildings.",
            "Drive carefully, especially on exposed roads and bridges.",
        ],
    },

    "extreme_heat": {
        "title": "Extreme Heat Advisory",
        "advice": [
            "Avoid prolonged exposure to direct sunlight.",
            "Drink sufficient water and stay hydrated.",
            "Avoid strenuous outdoor activities during the hottest hours.",
            "Wear lightweight and breathable clothing.",
            "Check on children and elderly people during extreme heat.",
        ],
    },

    "heat": {
        "title": "Heat Advisory",
        "advice": [
            "Stay hydrated throughout the day.",
            "Limit prolonged exposure to direct sunlight.",
            "Prefer cooler or shaded areas during the afternoon.",
        ],
    },

    "extreme_cold": {
        "title": "Extreme Cold Advisory",
        "advice": [
            "Keep yourself warm and avoid prolonged exposure to cold weather.",
            "Wear adequate warm clothing.",
            "Take extra care of children and elderly people.",
            "Avoid unnecessary travel in severe cold conditions.",
        ],
    },

    "cold": {
        "title": "Cold Weather Advisory",
        "advice": [
            "Wear warm clothing when going outside.",
            "Keep yourself adequately hydrated and warm.",
            "Take extra care during early morning and nighttime.",
        ],
    },

    "low_visibility": {
        "title": "Low Visibility Advisory",
        "advice": [
            "Drive slowly and maintain a safe distance.",
            "Use appropriate vehicle lights.",
            "Avoid unnecessary travel if visibility becomes dangerously low.",
            "Follow local traffic and weather warnings.",
        ],
    },
}


# =========================================================
# SEVERITY INTRODUCTION
# =========================================================

SEVERITY_MESSAGES = {

    "NONE": "No significant weather hazards have been detected.",

    "LOW": "Minor weather-related precautions are recommended.",

    "MODERATE": "Moderate weather conditions may require some precautions.",

    "HIGH": "Potentially hazardous weather conditions are expected. Please take precautions.",

    "SEVERE": "Severe weather conditions are expected. Please take immediate precautions.",
}


# =========================================================
# GENERAL ADVISORY
# =========================================================

GENERAL_ADVICE = [
    "Monitor updated weather information.",
    "Follow official local weather warnings when available.",
]


# =========================================================
# GENERATE ADVISORY
# =========================================================

def generate_advisory(alert_result):
    """
    Convert alert detection result into an advisory.

    Parameters
    ----------
    alert_result : dict
        Output returned by detect_alerts()

    Returns
    -------
    dict
        Structured advisory result.
    """

    if not isinstance(alert_result, dict):

        return {
            "status": "error",
            "severity": "UNKNOWN",
            "title": "Weather Advisory",
            "message": "Weather advisory data is unavailable.",
            "recommendations": [],
        }

    severity = alert_result.get(
        "highest_severity",
        "NONE"
    )

    alerts = alert_result.get(
        "alerts",
        []
    )

    recommendations = []
    titles = []

    # -----------------------------------------------------
    # Process each alert
    # -----------------------------------------------------

    for alert in alerts:

        alert_type = alert.get("type")

        rule = ADVISORY_RULES.get(
            alert_type
        )

        if not rule:
            continue

        title = rule.get(
            "title"
        )

        if title and title not in titles:
            titles.append(title)

        for advice in rule.get(
            "advice",
            []
        ):

            if advice not in recommendations:
                recommendations.append(
                    advice
                )

    # -----------------------------------------------------
    # Add general advice
    # -----------------------------------------------------

    for advice in GENERAL_ADVICE:

        if advice not in recommendations:
            recommendations.append(
                advice
            )

    # -----------------------------------------------------
    # Create message
    # -----------------------------------------------------

    message = SEVERITY_MESSAGES.get(
        severity,
        SEVERITY_MESSAGES["NONE"]
    )

    # -----------------------------------------------------
    # Return structured result
    # -----------------------------------------------------

    return {
        "status": "success",
        "severity": severity,
        "alert_count": len(alerts),
        "titles": titles,
        "message": message,
        "recommendations": recommendations,
    }


# =========================================================
# SIMPLE TEXT FORMATTER
# =========================================================

def format_advisory(advisory_result):
    """
    Convert structured advisory into readable text.
    """

    if not isinstance(
        advisory_result,
        dict
    ):
        return "Weather advisory is unavailable."

    if advisory_result.get(
        "status"
    ) != "success":
        return advisory_result.get(
            "message",
            "Weather advisory is unavailable."
        )

    severity = advisory_result.get(
        "severity",
        "NONE"
    )

    message = advisory_result.get(
        "message",
        ""
    )

    titles = advisory_result.get(
        "titles",
        []
    )

    recommendations = advisory_result.get(
        "recommendations",
        []
    )

    lines = []

    lines.append(
        f"⚠️ Weather Risk Level: {severity}"
    )

    lines.append("")

    if titles:
        lines.append(
            "Alerts:"
        )

        for title in titles:
            lines.append(
                f"• {title}"
            )

        lines.append("")

    lines.append(
        message
    )

    lines.append("")

    if recommendations:

        lines.append(
            "Recommended Precautions:"
        )

        for recommendation in recommendations:

            lines.append(
                f"• {recommendation}"
            )

    return "\n".join(lines)


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    from app.intelligence.alert_detector import (
        detect_alerts
    )

    print("=" * 60)
    print("WeatherGPT - Advisory Generator")
    print("=" * 60)

    # Sample dangerous weather
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
    # STEP 1: Detect alerts
    # -----------------------------------------------------

    alert_result = detect_alerts(
        sample_weather
    )

    # -----------------------------------------------------
    # STEP 2: Generate advisory
    # -----------------------------------------------------

    advisory_result = generate_advisory(
        alert_result
    )

    # -----------------------------------------------------
    # Print structured result
    # -----------------------------------------------------

    print("\nADVISORY RESULT")
    print("-" * 60)

    print(advisory_result)

    # -----------------------------------------------------
    # Print readable advisory
    # -----------------------------------------------------

    print("\nREADABLE ADVISORY")
    print("-" * 60)

    print(
        format_advisory(
            advisory_result
        )
    )