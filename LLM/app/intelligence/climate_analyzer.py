from statistics import mean


def analyze_climate(data):
    """
    Analyze historical climate data.

    Expected input:
    {
        "temperatures": [28.5, 29.1, 30.2],
        "rainfall": [5.2, 10.4, 2.1],
        "humidity": [70, 75, 78]
    }
    """

    if not isinstance(data, dict):
        return {
            "status": "error",
            "message": "Climate data must be a dictionary."
        }

    temperatures = data.get("temperatures", [])
    rainfall = data.get("rainfall", [])
    humidity = data.get("humidity", [])

    result = {
        "status": "success",
        "temperature": {},
        "rainfall": {},
        "humidity": {},
        "trends": []
    }

    # -----------------------------------------
    # Temperature Analysis
    # -----------------------------------------

    if temperatures:

        average_temperature = mean(temperatures)
        maximum_temperature = max(temperatures)
        minimum_temperature = min(temperatures)

        result["temperature"] = {
            "average_c": round(average_temperature, 2),
            "maximum_c": round(maximum_temperature, 2),
            "minimum_c": round(minimum_temperature, 2)
        }

        if len(temperatures) >= 2:

            if temperatures[-1] > temperatures[0]:
                result["trends"].append(
                    "Temperature is increasing."
                )

            elif temperatures[-1] < temperatures[0]:
                result["trends"].append(
                    "Temperature is decreasing."
                )

            else:
                result["trends"].append(
                    "Temperature is relatively stable."
                )

    # -----------------------------------------
    # Rainfall Analysis
    # -----------------------------------------

    if rainfall:

        average_rainfall = mean(rainfall)
        maximum_rainfall = max(rainfall)
        minimum_rainfall = min(rainfall)

        result["rainfall"] = {
            "average_mm": round(average_rainfall, 2),
            "maximum_mm": round(maximum_rainfall, 2),
            "minimum_mm": round(minimum_rainfall, 2)
        }

        if len(rainfall) >= 2:

            if rainfall[-1] > rainfall[0]:
                result["trends"].append(
                    "Rainfall is increasing."
                )

            elif rainfall[-1] < rainfall[0]:
                result["trends"].append(
                    "Rainfall is decreasing."
                )

            else:
                result["trends"].append(
                    "Rainfall is relatively stable."
                )

    # -----------------------------------------
    # Humidity Analysis
    # -----------------------------------------

    if humidity:

        average_humidity = mean(humidity)
        maximum_humidity = max(humidity)
        minimum_humidity = min(humidity)

        result["humidity"] = {
            "average_percent": round(average_humidity, 2),
            "maximum_percent": round(maximum_humidity, 2),
            "minimum_percent": round(minimum_humidity, 2)
        }

    return result


def print_climate_analysis(result):
    """Print climate analysis in a readable format."""

    print("\n======================================")
    print("         CLIMATE ANALYSIS")
    print("======================================")

    if result["status"] != "success":
        print("Error:", result["message"])
        return

    if result["temperature"]:
        print("\nTemperature:")
        print(
            "Average:",
            result["temperature"]["average_c"],
            "°C"
        )
        print(
            "Maximum:",
            result["temperature"]["maximum_c"],
            "°C"
        )
        print(
            "Minimum:",
            result["temperature"]["minimum_c"],
            "°C"
        )

    if result["rainfall"]:
        print("\nRainfall:")
        print(
            "Average:",
            result["rainfall"]["average_mm"],
            "mm"
        )
        print(
            "Maximum:",
            result["rainfall"]["maximum_mm"],
            "mm"
        )
        print(
            "Minimum:",
            result["rainfall"]["minimum_mm"],
            "mm"
        )

    if result["humidity"]:
        print("\nHumidity:")
        print(
            "Average:",
            result["humidity"]["average_percent"],
            "%"
        )
        print(
            "Maximum:",
            result["humidity"]["maximum_percent"],
            "%"
        )
        print(
            "Minimum:",
            result["humidity"]["minimum_percent"],
            "%"
        )

    if result["trends"]:
        print("\nTrends:")

        for trend in result["trends"]:
            print("-", trend)


if __name__ == "__main__":

    sample_data = {
        "temperatures": [
            27.5,
            28.2,
            29.1,
            30.4,
            31.0
        ],
        "rainfall": [
            4.2,
            6.5,
            8.1,
            10.2,
            12.4
        ],
        "humidity": [
            68,
            71,
            74,
            76,
            79
        ]
    }

    result = analyze_climate(sample_data)

    print_climate_analysis(result)