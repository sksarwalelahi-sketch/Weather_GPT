# app/tools/tool_runner.py

"""
WeatherGPT - Tool Runner

This file connects:
    Analyzer -> Selector -> Weather Tools

It executes the tool selected by selector.py.
"""

from app.tools.weather_tools import (
    get_current_weather,
    get_forecast,
    get_alerts,
    get_flood_data,
    get_climate_analysis,
    get_agriculture_advisory,
    get_aviation_advisory,
    get_marine_advisory,
)


def run_selected_tool(
    analysis: dict,
    selected_tool: str,
    climate_request: dict | None = None,
) -> dict:
    """
    Execute the tool selected by selector.py.
    """

    location = analysis.get("location")
    time = analysis.get("time", "tomorrow")

    if not location:
        return {
            "status": "error",
            "message": "Location was not provided."
        }

    if selected_tool == "get_current_weather":
        return get_current_weather(location)

    elif selected_tool == "get_forecast":
        return get_forecast(location, time)

    elif selected_tool == "get_alerts":
        return get_alerts(location)

    elif selected_tool == "get_flood_data":
        return get_flood_data(location)

    elif selected_tool == "get_climate_analysis":
        climate_request = climate_request or {}

        return get_climate_analysis(
            location,
            start_date=climate_request.get("start_date"),
            end_date=climate_request.get("end_date"),
            baselines=climate_request.get("baselines"),
        )

    elif selected_tool == "get_agriculture_advisory":
        return get_agriculture_advisory(location)

    elif selected_tool == "get_aviation_advisory":
        return get_aviation_advisory(location)

    elif selected_tool == "get_marine_advisory":
        return get_marine_advisory(location)

    else:
        return {
            "status": "error",
            "message": f"Unknown tool: {selected_tool}"
        }


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    print("\n===== TOOL RUNNER TEST =====")

    # Example output from analyzer.py
    analysis = {
        "intent": "forecast",
        "location": "Bhubaneswar",
        "time": "tomorrow",
        "language": "English",
        "parameters": [
            "precipitation_probability"
        ]
    }

    # Example output from selector.py
    selected_tool = "get_forecast"

    print("\nAnalysis:")
    print(analysis)

    print("\nSelected Tool:")
    print(selected_tool)

    result = run_selected_tool(
        analysis,
        selected_tool
    )

    print("\nTool Result:")
    print(result)

    print("\n===== TEST COMPLETE =====")
