"""
WeatherGPT - Weather Intelligence Coordinator

Member 2: AI / LLM / Weather Intelligence

Combines:
    1. Forecast Analysis
    2. Alert Detection
    3. Risk Scoring
    4. Advisory Generation
"""

from app.intelligence.forecast_analyzer import (
    analyze_forecast
)

from app.intelligence.alert_detector import (
    detect_alerts
)

from app.intelligence.risk_scorer import (
    calculate_risk
)

from app.intelligence.advisory_generator import (
    generate_advisory
)

from app.intelligence.advisory_generator import (
    format_advisory
)


# =========================================================
# MAIN WEATHER INTELLIGENCE
# =========================================================

def analyze_weather_intelligence(weather_data):
    """
    Run the complete WeatherGPT intelligence pipeline.

    Parameters
    ----------
    weather_data : dict
        Structured weather information.

    Returns
    -------
    dict
        Complete weather intelligence result.
    """

    if not isinstance(weather_data, dict):

        return {
            "status": "error",
            "message": "Invalid weather data.",
        }

    # =====================================================
    # STEP 1 - FORECAST ANALYSIS
    # =====================================================

    forecast_result = analyze_forecast(
        weather_data
    )

    # =====================================================
    # STEP 2 - ALERT DETECTION
    # =====================================================

    alert_result = detect_alerts(
        weather_data
    )

    # =====================================================
    # STEP 3 - RISK SCORING
    # =====================================================

    risk_result = calculate_risk(
        weather_data,
        alert_result
    )

    # =====================================================
    # STEP 4 - ADVISORY GENERATION
    # =====================================================

    advisory_result = generate_advisory(
        alert_result
    )

    # =====================================================
    # FORMAT READABLE ADVISORY
    # =====================================================

    advisory_text = format_advisory(
        advisory_result
    )

    # =====================================================
    # FINAL RESULT
    # =====================================================

    return {
        "status": "success",

        "forecast_analysis": forecast_result,

        "alerts": alert_result,

        "risk": risk_result,

        "advisory": advisory_result,

        "advisory_text": advisory_text,
    }


# =========================================================
# SIMPLE SUMMARY
# =========================================================

def get_intelligence_summary(result):
    """
    Generate a short summary from intelligence result.
    """

    if not isinstance(result, dict):

        return "Weather intelligence unavailable."

    if result.get("status") != "success":

        return result.get(
            "message",
            "Weather intelligence unavailable."
        )

    risk = result.get(
        "risk",
        {}
    )

    alerts = result.get(
        "alerts",
        {}
    )

    score = risk.get(
        "score",
        0
    )

    level = risk.get(
        "level",
        "LOW"
    )

    alert_count = alerts.get(
        "alert_count",
        0
    )

    return (
        f"Weather risk level is {level} "
        f"with a risk score of {score}/100. "
        f"{alert_count} weather alert(s) detected."
    )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print("=" * 65)
    print("WeatherGPT - Complete Weather Intelligence")
    print("=" * 65)

    # -----------------------------------------------------
    # Sample weather
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
    # Run complete intelligence
    # -----------------------------------------------------

    result = analyze_weather_intelligence(
        sample_weather
    )

    # -----------------------------------------------------
    # Print summary
    # -----------------------------------------------------

    print("\nINTELLIGENCE SUMMARY")
    print("-" * 65)

    print(
        get_intelligence_summary(
            result
        )
    )

    # -----------------------------------------------------
    # Forecast
    # -----------------------------------------------------

    print("\nFORECAST ANALYSIS")
    print("-" * 65)

    print(
        result[
            "forecast_analysis"
        ]
    )

    # -----------------------------------------------------
    # Alerts
    # -----------------------------------------------------

    print("\nALERTS")
    print("-" * 65)

    print(
        result[
            "alerts"
        ]
    )

    # -----------------------------------------------------
    # Risk
    # -----------------------------------------------------

    print("\nRISK")
    print("-" * 65)

    print(
        result[
            "risk"
        ]
    )

    # -----------------------------------------------------
    # Advisory
    # -----------------------------------------------------

    print("\nADVISORY")
    print("-" * 65)

    print(
        result[
            "advisory_text"
        ]
    )

    # -----------------------------------------------------
    # Full result
    # -----------------------------------------------------

    print("\nCOMPLETE RESULT")
    print("-" * 65)

    print(result)