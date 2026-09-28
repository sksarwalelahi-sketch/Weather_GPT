# app/response/weather_interpreter.py

"""
WeatherGPT - Weather Data Interpreter

Converts raw weather API data into clear,
deterministic weather facts.

Python decides factual weather information.
The response generator converts those facts
into natural language.
"""


def interpret_weather(tool_result: dict) -> dict:

    data = tool_result.get("data", {})

    # -----------------------------------------------------
    # Basic weather values
    # -----------------------------------------------------

    condition = data.get("condition")

    rain_probability = data.get("rain_probability")

    rainfall = data.get("rainfall_mm")

    precipitation = data.get("precipitation_mm")

    temperature = data.get("temperature_c")

    temperature_max = data.get("temperature_max_c")

    temperature_min = data.get("temperature_min_c")

    # IMPORTANT:
    # Read humidity from the weather API.
    humidity = data.get("humidity")

    # -----------------------------------------------------
    # Determine whether rain is expected
    # -----------------------------------------------------

    rain_expected = False

    if rain_probability is not None:

        try:
            if float(rain_probability) >= 50:
                rain_expected = True
        except (TypeError, ValueError):
            pass

    # -----------------------------------------------------
    # Determine rain intensity
    # -----------------------------------------------------

    rain_intensity = "unknown"

    # Prefer rainfall_mm when available.
    rain_amount = rainfall

    # If rainfall_mm is missing, use precipitation_mm.
    if rain_amount is None:
        rain_amount = precipitation

    if rain_amount is not None:

        try:
            rain_amount = float(rain_amount)

            if rain_amount <= 0:
                rain_intensity = "none"

            elif rain_amount < 2.5:
                rain_intensity = "light"

            elif rain_amount < 10:
                rain_intensity = "moderate"

            else:
                rain_intensity = "heavy"

        except (TypeError, ValueError):
            rain_intensity = "unknown"

    # -----------------------------------------------------
    # Determine heavy rain
    # -----------------------------------------------------

    heavy_rain = False

    if rain_amount is not None:

        try:
            if float(rain_amount) >= 10:
                heavy_rain = True
        except (TypeError, ValueError):
            pass

    # Also detect heavy rain from weather condition.
    if condition:

        condition_text = str(condition).lower()

        heavy_keywords = [
            "heavy rain",
            "heavy rainfall",
            "thunderstorm",
            "torrential",
            "violent rain",
            "downpour",
        ]

        for keyword in heavy_keywords:

            if keyword in condition_text:
                heavy_rain = True
                break

    # -----------------------------------------------------
    # Build structured facts
    # -----------------------------------------------------

    facts = {

        "location": tool_result.get("location"),

        "time": tool_result.get("time"),

        "condition": condition,

        "rain_expected": rain_expected,

        "rain_probability": rain_probability,

        "rainfall_mm": rainfall,

        "precipitation_mm": precipitation,

        "rain_intensity": rain_intensity,

        "heavy_rain": heavy_rain,

        "temperature_c": temperature,

        "temperature_max_c": temperature_max,

        "temperature_min_c": temperature_min,

        # NEW
        "humidity": humidity,
    }

    return facts


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    sample_data = {

        "tool": "get_forecast",

        "location": "Bhubaneswar",

        "time": "tomorrow",

        "status": "live_data",

        "data": {

            "temperature_max_c": 32.6,

            "temperature_min_c": 25.7,

            "condition": "Light drizzle",

            "rain_probability": 68,

            "precipitation_mm": 1.1,

            "rainfall_mm": 0.8,

            "humidity": 78
        }
    }

    result = interpret_weather(sample_data)

    print("\n======================================")
    print("     Weather Data Interpreter")
    print("======================================")

    print("\nInterpreted Weather Facts:")

    for key, value in result.items():

        print(f"{key}: {value}")

    print("\n======================================")
    print("          TEST COMPLETE")
    print("======================================")