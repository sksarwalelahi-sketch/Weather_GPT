# app/tools/selector.py

"""
WeatherGPT - Tool Selector

Takes the detected intent and selects
the correct WeatherGPT tool.
"""


def select_tool(analysis: dict) -> str:
    """
    Select the appropriate WeatherGPT tool
    based on detected intent.
    """

    intent = analysis.get("intent", "").lower().strip()

    tool_mapping = {

        # Current weather
        "weather": "get_current_weather",
        "current_weather": "get_current_weather",

        # Forecast
        "forecast": "get_forecast",

        # Alerts
        "alert": "get_alerts",
        "alerts": "get_alerts",
        "flood": "get_flood_data",
        "flooding": "get_flood_data",

        # Safety
        "safety": "get_alerts",

        # Climate
        "climate": "get_climate_analysis",

        # Agriculture
        "agriculture": "get_agriculture_advisory",

        # Aviation
        "aviation": "get_aviation_advisory",

        # Marine
        "marine": "get_marine_advisory",

        # General knowledge
        "knowledge": "general_weather",

        # Location
        "location": "general_weather",
    }

    return tool_mapping.get(intent, "general_weather")


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    test_cases = [

        {
            "intent": "weather",
            "location": "Delhi"
        },

        {
            "intent": "forecast",
            "location": "Bhubaneswar",
            "time": "tomorrow"
        },

        {
            "intent": "alert",
            "location": "Odisha"
        },

        {
            "intent": "safety",
            "location": "Odisha"
        },

        {
            "intent": "climate",
            "location": "Mumbai"
        },

        {
            "intent": "agriculture",
            "location": "Ranchi"
        },

        {
            "intent": "aviation",
            "location": "Delhi"
        },

        {
            "intent": "marine",
            "location": "Chennai"
        },

        {
            "intent": "knowledge",
            "location": None
        }
    ]

    print("======================================")
    print("       WeatherGPT Tool Selector")
    print("======================================")

    for analysis in test_cases:

        tool = select_tool(analysis)

        print("\nAnalysis:", analysis)
        print("Selected Tool:", tool)