from app.tools.climate_tools import get_historical_weather
from app.intelligence.climate_analyzer import analyze_climate


def analyze_historical_climate(location, start_date, end_date):
    """
    Fetch historical weather data and analyze its climate trends.
    """

    # -----------------------------------------
    # Step 1: Fetch historical data
    # -----------------------------------------

    weather_data = get_historical_weather(
        location,
        start_date,
        end_date
    )

    # -----------------------------------------
    # Check API result
    # -----------------------------------------

    if weather_data.get("status") != "live_data":

        return {
            "status": "error",
            "message": weather_data.get(
                "message",
                "Unable to fetch historical climate data."
            )
        }

    # -----------------------------------------
    # Step 2: Prepare data for analyzer
    # -----------------------------------------

    climate_input = {
        "temperatures": weather_data.get(
            "temperatures",
            []
        ),

        "rainfall": weather_data.get(
            "rainfall",
            [] 
        )
    }

    # -----------------------------------------
    # Step 3: Analyze climate
    # -----------------------------------------

    analysis = analyze_climate(climate_input)

    # -----------------------------------------
    # Step 4: Combine API + analysis
    # -----------------------------------------

    return {
        "status": "success",

        "location": weather_data.get(
            "location"
        ),

        "country": weather_data.get(
            "country"
        ),

        "start_date": weather_data.get(
            "start_date"
        ),

        "end_date": weather_data.get(
            "end_date"
        ),

        "days": len(
            weather_data.get("dates", [])
        ),

        "climate_analysis": analysis
    }


def print_climate_result(result):
    """
    Display the final climate analysis.
    """

    print("\n======================================")
    print("     HISTORICAL CLIMATE ANALYSIS")
    print("======================================")

    if result.get("status") != "success":

        print(
            "\nERROR:",
            result.get("message")
        )

        return

    print(
        "\nLocation:",
        result.get("location")
    )

    print(
        "Country:",
        result.get("country")
    )

    print(
        "Period:",
        result.get("start_date"),
        "to",
        result.get("end_date")
    )

    print(
        "Number of days:",
        result.get("days")
    )

    analysis = result.get(
        "climate_analysis",
        {}
    )

    # -----------------------------------------
    # Temperature
    # -----------------------------------------

    temperature = analysis.get(
        "temperature",
        {}
    )

    if temperature:

        print("\nTemperature:")

        print(
            "Average:",
            temperature.get("average_c"),
            "°C"
        )

        print(
            "Maximum:",
            temperature.get("maximum_c"),
            "°C"
        )

        print(
            "Minimum:",
            temperature.get("minimum_c"),
            "°C"
        )

    # -----------------------------------------
    # Rainfall
    # -----------------------------------------

    rainfall = analysis.get(
        "rainfall",
        {}
    )

    if rainfall:

        print("\nRainfall:")

        print(
            "Average:",
            rainfall.get("average_mm"),
            "mm"
        )

        print(
            "Maximum:",
            rainfall.get("maximum_mm"),
            "mm"
        )

        print(
            "Minimum:",
            rainfall.get("minimum_mm"),
            "mm"
        )

    # -----------------------------------------
    # Trends
    # -----------------------------------------

    trends = analysis.get(
        "trends",
        []
    )

    if trends:

        print("\nTrends:")

        for trend in trends:

            print(
                "-",
                trend
            )


# =============================================
# TEST
# =============================================

if __name__ == "__main__":

    result = analyze_historical_climate(
        location="Delhi",
        start_date="2026-08-07",
        end_date="2026-09-06"
    )

    print_climate_result(result)