"""
WeatherGPT - Forecast Intelligence Engine

Member 2: AI / LLM / RAG / Weather Intelligence

This module converts raw weather data into structured
weather intelligence.

It does NOT call any external API.
It only analyzes weather data received from the weather tools.
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
# RAIN SEVERITY
# =========================================================

def calculate_rain_severity(rainfall):
    """
    Estimate rainfall severity from rainfall amount in mm.

    These are simple rule-based thresholds for the
    WeatherGPT intelligence layer.
    """

    rainfall = to_float(rainfall)

    if rainfall is None:
        return "unknown"

    if rainfall <= 0:
        return "none"

    if rainfall < 2.5:
        return "light"

    if rainfall < 10:
        return "moderate"

    if rainfall < 20:
        return "heavy"

    return "very_heavy"


# =========================================================
# RAIN EXPECTATION
# =========================================================

def calculate_rain_expectation(rain_probability, rainfall):
    """Determine whether meaningful rain is expected."""

    probability = to_float(rain_probability)
    rainfall = to_float(rainfall)

    if rainfall is not None and rainfall >= 10:
        return True

    if probability is not None and probability >= 50:
        return True

    if rainfall is not None and rainfall > 0:
        return True

    return False


# =========================================================
# THUNDERSTORM DETECTION
# =========================================================

def detect_thunderstorm(condition):
    """Detect thunderstorm-related conditions."""

    if not condition:
        return False

    condition_text = str(condition).lower()

    thunderstorm_keywords = [
        "thunderstorm",
        "thunder storm",
        "storm",
        "lightning",
        "t-storm",
    ]

    return any(
        keyword in condition_text
        for keyword in thunderstorm_keywords
    )


# =========================================================
# HEAVY RAIN DETECTION
# =========================================================

def detect_heavy_rain(rainfall, condition=None):
    """Detect heavy rainfall from amount or weather condition."""

    rainfall = to_float(rainfall)

    if rainfall is not None and rainfall >= 10:
        return True

    if condition:
        condition_text = str(condition).lower()

        heavy_keywords = [
            "heavy rain",
            "heavy rainfall",
            "torrential",
            "downpour",
            "violent rain",
            "very heavy rain",
        ]

        if any(
            keyword in condition_text
            for keyword in heavy_keywords
        ):
            return True

    return False


# =========================================================
# STRONG WIND DETECTION
# =========================================================

def detect_strong_wind(wind_speed):
    """Detect strong wind conditions."""

    wind_speed = to_float(wind_speed)

    if wind_speed is None:
        return False

    # Simple rule-based threshold.
    return wind_speed >= 40


# =========================================================
# EXTREME HEAT DETECTION
# =========================================================

def detect_extreme_heat(temperature):
    """Detect potentially extreme temperature."""

    temperature = to_float(temperature)

    if temperature is None:
        return False

    return temperature >= 40


# =========================================================
# EXTREME COLD DETECTION
# =========================================================

def detect_extreme_cold(temperature):
    """Detect potentially very cold conditions."""

    temperature = to_float(temperature)

    if temperature is None:
        return False

    return temperature <= 5


# =========================================================
# RAIN RISK SCORE
# =========================================================

def calculate_rain_risk(rain_probability, rainfall):
    """
    Calculate a rain risk score from 0 to 100.
    """

    probability = to_float(rain_probability)
    rainfall = to_float(rainfall)

    score = 0

    # Probability contribution
    if probability is not None:
        score += probability * 0.6

    # Rainfall contribution
    if rainfall is not None:

        if rainfall >= 50:
            score += 40

        elif rainfall >= 30:
            score += 35

        elif rainfall >= 20:
            score += 30

        elif rainfall >= 10:
            score += 25

        elif rainfall >= 5:
            score += 15

        elif rainfall > 0:
            score += 5

    score = round(score)

    return min(score, 100)


# =========================================================
# OVERALL RISK SCORE
# =========================================================

def calculate_overall_risk(
    rain_probability=None,
    rainfall=None,
    wind_speed=None,
    temperature=None,
    condition=None,
):
    """
    Calculate an overall weather risk score from 0 to 100.
    """

    score = calculate_rain_risk(
        rain_probability,
        rainfall
    )

    # Thunderstorm increases risk
    if detect_thunderstorm(condition):
        score += 20

    # Strong wind
    if detect_strong_wind(wind_speed):
        score += 15

    # Extreme heat
    if detect_extreme_heat(temperature):
        score += 15

    # Extreme cold
    if detect_extreme_cold(temperature):
        score += 10

    return min(round(score), 100)


# =========================================================
# RISK LEVEL
# =========================================================

def risk_level(score):
    """Convert numeric score into human-readable risk level."""

    score = to_float(score)

    if score is None:
        return "UNKNOWN"

    if score <= 30:
        return "LOW"

    if score <= 60:
        return "MODERATE"

    if score <= 80:
        return "HIGH"

    return "SEVERE"


# =========================================================
# FORECAST ANALYSIS
# =========================================================

def analyze_forecast(weather_data):
    """
    Analyze raw weather data.

    Accepts the data dictionary returned by WeatherGPT's
    weather tools.

    Returns a structured intelligence dictionary.
    """

    if not isinstance(weather_data, dict):
        return {
            "status": "error",
            "message": "Invalid weather data"
        }

    # -----------------------------------------------------
    # Read weather values
    # -----------------------------------------------------

    temperature = weather_data.get("temperature_c")

    temperature_max = weather_data.get(
        "temperature_max_c"
    )

    temperature_min = weather_data.get(
        "temperature_min_c"
    )

    rainfall = weather_data.get("rainfall_mm")

    precipitation = weather_data.get(
        "precipitation_mm"
    )

    rain_probability = weather_data.get(
        "rain_probability"
    )

    humidity = weather_data.get(
        "humidity"
    )

    wind_speed = weather_data.get(
        "wind_speed_kmh"
    )

    condition = weather_data.get(
        "condition"
    )

    # -----------------------------------------------------
    # Rainfall fallback
    # -----------------------------------------------------

    if rainfall is None:
        rainfall = precipitation

    # -----------------------------------------------------
    # Rain analysis
    # -----------------------------------------------------

    rain_expected = calculate_rain_expectation(
        rain_probability,
        rainfall
    )

    rain_severity = calculate_rain_severity(
        rainfall
    )

    heavy_rain = detect_heavy_rain(
        rainfall,
        condition
    )

    # -----------------------------------------------------
    # Weather event detection
    # -----------------------------------------------------

    thunderstorm = detect_thunderstorm(
        condition
    )

    strong_wind = detect_strong_wind(
        wind_speed
    )

    extreme_heat = detect_extreme_heat(
        temperature
    )

    extreme_cold = detect_extreme_cold(
        temperature
    )

    # -----------------------------------------------------
    # Risk
    # -----------------------------------------------------

    overall_score = calculate_overall_risk(
        rain_probability=rain_probability,
        rainfall=rainfall,
        wind_speed=wind_speed,
        temperature=temperature,
        condition=condition,
    )

    overall_level = risk_level(
        overall_score
    )

    # -----------------------------------------------------
    # Return structured intelligence
    # -----------------------------------------------------

    return {
        "status": "success",

        "weather": {
            "temperature_c": temperature,
            "temperature_min_c": temperature_min,
            "temperature_max_c": temperature_max,
            "rain_probability": rain_probability,
            "rainfall_mm": rainfall,
            "humidity": humidity,
            "wind_speed_kmh": wind_speed,
            "condition": condition,
        },

        "rain_analysis": {
            "rain_expected": rain_expected,
            "rain_severity": rain_severity,
            "heavy_rain": heavy_rain,
        },

        "hazards": {
            "thunderstorm": thunderstorm,
            "strong_wind": strong_wind,
            "extreme_heat": extreme_heat,
            "extreme_cold": extreme_cold,
        },

        "risk": {
            "score": overall_score,
            "level": overall_level,
        },
    }


# =========================================================
# TESTING
# =========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("WeatherGPT - Forecast Intelligence Engine")
    print("=" * 60)

    sample_weather = {
        "temperature_max_c": 32.6,
        "temperature_min_c": 25.7,
        "rain_probability": 85,
        "precipitation_mm": 25.0,
        "rainfall_mm": 20.0,
        "humidity": 82,
        "wind_speed_kmh": 45,
        "condition": "Thunderstorm",
    }

    result = analyze_forecast(
        sample_weather
    )

    print("\nFORECAST INTELLIGENCE")
    print("-" * 60)

    print(
        "Rain Expected:",
        result["rain_analysis"]["rain_expected"]
    )

    print(
        "Rain Severity:",
        result["rain_analysis"]["rain_severity"]
    )

    print(
        "Heavy Rain:",
        result["rain_analysis"]["heavy_rain"]
    )

    print(
        "Thunderstorm:",
        result["hazards"]["thunderstorm"]
    )

    print(
        "Strong Wind:",
        result["hazards"]["strong_wind"]
    )

    print(
        "Risk Score:",
        result["risk"]["score"]
    )

    print(
        "Risk Level:",
        result["risk"]["level"]
    )

    print("\nFull Result:")
    print(result)