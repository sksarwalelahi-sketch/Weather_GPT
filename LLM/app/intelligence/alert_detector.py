"""
WeatherGPT - Alert Detection Engine

Member 2: AI / LLM / Weather Intelligence

This module detects potentially dangerous weather
conditions from structured weather intelligence.

It does not call external APIs.
"""


# =========================================================
# SAFE NUMBER CONVERSION
# =========================================================

def to_float(value):
    """Convert a value to float safely."""

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# =========================================================
# ALERT CREATOR
# =========================================================

def create_alert(
    alert_type,
    severity,
    message,
    value=None,
    unit=None,
):
    """Create a standard WeatherGPT alert."""

    return {
        "type": alert_type,
        "severity": severity,
        "message": message,
        "value": value,
        "unit": unit,
    }


# =========================================================
# HEAVY RAIN ALERT
# =========================================================

def detect_heavy_rain_alert(
    rainfall=None,
    rain_probability=None,
    condition=None,
):
    """Detect heavy or very heavy rainfall."""

    rainfall = to_float(rainfall)
    probability = to_float(rain_probability)

    condition_text = str(condition or "").lower()

    heavy_condition = any(
        word in condition_text
        for word in [
            "heavy rain",
            "heavy rainfall",
            "very heavy rain",
            "torrential",
            "downpour",
        ]
    )

    # Very heavy rainfall
    if rainfall is not None and rainfall >= 20:
        return create_alert(
            "heavy_rain",
            "SEVERE",
            "Very heavy rainfall is expected.",
            rainfall,
            "mm",
        )

    # Heavy rainfall
    if rainfall is not None and rainfall >= 10:
        return create_alert(
            "heavy_rain",
            "HIGH",
            "Heavy rainfall is expected.",
            rainfall,
            "mm",
        )

    # Condition-based detection
    if heavy_condition:
        return create_alert(
            "heavy_rain",
            "HIGH",
            "Heavy rainfall conditions are expected.",
            rainfall,
            "mm",
        )

    # High probability + moderate rainfall
    if (
        probability is not None
        and probability >= 80
        and rainfall is not None
        and rainfall >= 5
    ):
        return create_alert(
            "heavy_rain",
            "HIGH",
            "High probability of significant rainfall.",
            probability,
            "%",
        )

    return None


# =========================================================
# THUNDERSTORM ALERT
# =========================================================

def detect_thunderstorm_alert(condition=None):
    """Detect thunderstorm conditions."""

    condition_text = str(condition or "").lower()

    keywords = [
        "thunderstorm",
        "thunder storm",
        "lightning",
        "t-storm",
    ]

    if any(
        keyword in condition_text
        for keyword in keywords
    ):
        return create_alert(
            "thunderstorm",
            "HIGH",
            "Thunderstorm activity is expected.",
        )

    return None


# =========================================================
# STRONG WIND ALERT
# =========================================================

def detect_strong_wind_alert(wind_speed=None):
    """Detect strong wind conditions."""

    wind_speed = to_float(wind_speed)

    if wind_speed is None:
        return None

    if wind_speed >= 60:
        return create_alert(
            "strong_wind",
            "SEVERE",
            "Very strong winds are expected.",
            wind_speed,
            "km/h",
        )

    if wind_speed >= 40:
        return create_alert(
            "strong_wind",
            "HIGH",
            "Strong winds are expected.",
            wind_speed,
            "km/h",
        )

    return None


# =========================================================
# EXTREME HEAT ALERT
# =========================================================

def detect_heat_alert(
    temperature=None,
    temperature_max=None,
):
    """Detect extreme heat conditions."""

    temperature = to_float(temperature)
    temperature_max = to_float(temperature_max)

    # Use maximum forecast temperature if available
    value = temperature_max

    if value is None:
        value = temperature

    if value is None:
        return None

    if value >= 45:
        return create_alert(
            "extreme_heat",
            "SEVERE",
            "Extreme heat conditions are expected.",
            value,
            "°C",
        )

    if value >= 40:
        return create_alert(
            "extreme_heat",
            "HIGH",
            "High temperature conditions are expected.",
            value,
            "°C",
        )

    if value >= 35:
        return create_alert(
            "heat",
            "MODERATE",
            "Hot weather conditions are expected.",
            value,
            "°C",
        )

    return None


# =========================================================
# EXTREME COLD ALERT
# =========================================================

def detect_cold_alert(
    temperature=None,
    temperature_min=None,
):
    """Detect extreme cold conditions."""

    temperature = to_float(temperature)
    temperature_min = to_float(temperature_min)

    value = temperature_min

    if value is None:
        value = temperature

    if value is None:
        return None

    if value <= 0:
        return create_alert(
            "extreme_cold",
            "SEVERE",
            "Extreme cold conditions are expected.",
            value,
            "°C",
        )

    if value <= 5:
        return create_alert(
            "extreme_cold",
            "HIGH",
            "Very cold conditions are expected.",
            value,
            "°C",
        )

    if value <= 10:
        return create_alert(
            "cold",
            "MODERATE",
            "Cold weather conditions are expected.",
            value,
            "°C",
        )

    return None


# =========================================================
# LOW VISIBILITY ALERT
# =========================================================

def detect_visibility_alert(visibility=None):
    """Detect dangerous low visibility."""

    visibility = to_float(visibility)

    if visibility is None:
        return None

    # Assuming visibility is provided in meters
    if visibility < 500:
        return create_alert(
            "low_visibility",
            "SEVERE",
            "Very low visibility conditions detected.",
            visibility,
            "m",
        )

    if visibility < 1000:
        return create_alert(
            "low_visibility",
            "HIGH",
            "Low visibility conditions detected.",
            visibility,
            "m",
        )

    return None


# =========================================================
# OVERALL ALERT DETECTION
# =========================================================

def detect_alerts(weather_data):
    """
    Analyze weather data and return all detected alerts.
    """

    if not isinstance(weather_data, dict):
        return {
            "status": "error",
            "alerts": [],
            "alert_count": 0,
            "highest_severity": "UNKNOWN",
        }

    # -----------------------------------------------------
    # Extract data
    # -----------------------------------------------------

    temperature = weather_data.get(
        "temperature_c"
    )

    temperature_max = weather_data.get(
        "temperature_max_c"
    )

    temperature_min = weather_data.get(
        "temperature_min_c"
    )

    rainfall = weather_data.get(
        "rainfall_mm"
    )

    if rainfall is None:
        rainfall = weather_data.get(
            "precipitation_mm"
        )

    rain_probability = weather_data.get(
        "rain_probability"
    )

    wind_speed = weather_data.get(
        "wind_speed_kmh"
    )

    visibility = weather_data.get(
        "visibility"
    )

    condition = weather_data.get(
        "condition"
    )

    # -----------------------------------------------------
    # Detect alerts
    # -----------------------------------------------------

    alerts = []

    alert = detect_heavy_rain_alert(
        rainfall=rainfall,
        rain_probability=rain_probability,
        condition=condition,
    )

    if alert:
        alerts.append(alert)

    alert = detect_thunderstorm_alert(
        condition
    )

    if alert:
        alerts.append(alert)

    alert = detect_strong_wind_alert(
        wind_speed
    )

    if alert:
        alerts.append(alert)

    alert = detect_heat_alert(
        temperature=temperature,
        temperature_max=temperature_max,
    )

    if alert:
        alerts.append(alert)

    alert = detect_cold_alert(
        temperature=temperature,
        temperature_min=temperature_min,
    )

    if alert:
        alerts.append(alert)

    alert = detect_visibility_alert(
        visibility
    )

    if alert:
        alerts.append(alert)

    # -----------------------------------------------------
    # Determine highest severity
    # -----------------------------------------------------

    severity_rank = {
        "LOW": 1,
        "MODERATE": 2,
        "HIGH": 3,
        "SEVERE": 4,
    }

    highest_severity = "LOW"

    for alert in alerts:

        current = alert.get(
            "severity",
            "LOW"
        )

        if (
            severity_rank.get(current, 0)
            >
            severity_rank.get(highest_severity, 0)
        ):
            highest_severity = current

    if not alerts:
        highest_severity = "NONE"

    # -----------------------------------------------------
    # Return
    # -----------------------------------------------------

    return {
        "status": "success",
        "alert_count": len(alerts),
        "highest_severity": highest_severity,
        "alerts": alerts,
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("WeatherGPT - Alert Detection Engine")
    print("=" * 60)

    sample_weather = {
        "temperature_max_c": 43.5,
        "temperature_min_c": 26.0,
        "rain_probability": 90,
        "rainfall_mm": 25.0,
        "humidity": 85,
        "wind_speed_kmh": 48,
        "condition": "Thunderstorm",
    }

    result = detect_alerts(
        sample_weather
    )

    print("\nALERT SUMMARY")
    print("-" * 60)

    print(
        "Alert Count:",
        result["alert_count"]
    )

    print(
        "Highest Severity:",
        result["highest_severity"]
    )

    print("\nDetected Alerts:")

    for alert in result["alerts"]:

        print(
            f"- {alert['type']} | "
            f"{alert['severity']} | "
            f"{alert['message']}"
        )

    print("\nFull Result:")
    print(result)