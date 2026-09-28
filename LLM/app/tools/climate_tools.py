import requests
from datetime import datetime, timedelta


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def get_location_coordinates(location):
    """
    Convert city/location name into latitude and longitude.
    """

    try:
        response = requests.get(
            GEOCODING_URL,
            params={
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json"
            },
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("results", [])

        if not results:
            return {
                "status": "error",
                "message": f"Location '{location}' not found."
            }

        place = results[0]

        return {
            "status": "success",
            "location": place.get("name"),
            "country": place.get("country"),
            "latitude": place.get("latitude"),
            "longitude": place.get("longitude")
        }

    except requests.RequestException as e:

        return {
            "status": "error",
            "message": f"Location API error: {e}"
        }


def get_historical_weather(location, start_date, end_date):
    """
    Fetch historical weather data for a location.

    start_date and end_date format:
    YYYY-MM-DD
    """

    # -----------------------------------------
    # Validate dates
    # -----------------------------------------

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

    except ValueError:

        return {
            "status": "error",
            "message": "Date must be in YYYY-MM-DD format."
        }

    if start > end:

        return {
            "status": "error",
            "message": "start_date cannot be after end_date."
        }

    # -----------------------------------------
    # Get coordinates
    # -----------------------------------------

    location_data = get_location_coordinates(location)

    if location_data["status"] != "success":
        return location_data

    latitude = location_data["latitude"]
    longitude = location_data["longitude"]

    # -----------------------------------------
    # Request historical weather
    # -----------------------------------------

    try:

        response = requests.get(
            ARCHIVE_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date,
                "end_date": end_date,

                "daily": ",".join([
                    "temperature_2m_mean",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "rain_sum"
                ]),

                "timezone": "auto"
            },

            timeout=30
        )

        response.raise_for_status()

        data = response.json()

    except requests.RequestException as e:

        return {
            "status": "error",
            "message": f"Historical weather API error: {e}"
        }

    # -----------------------------------------
    # Extract daily data
    # -----------------------------------------

    daily = data.get("daily")

    if not daily:

        return {
            "status": "error",
            "message": "No historical weather data available."
        }

    dates = daily.get("time", [])

    temperatures = daily.get(
        "temperature_2m_mean",
        []
    )

    maximum_temperatures = daily.get(
        "temperature_2m_max",
        []
    )

    minimum_temperatures = daily.get(
        "temperature_2m_min",
        []
    )

    precipitation = daily.get(
        "precipitation_sum",
        []
    )

    rainfall = daily.get(
        "rain_sum",
        []
    )

    # -----------------------------------------
    # Remove missing values
    # -----------------------------------------

    temperature_values = [
        value
        for value in temperatures
        if value is not None
    ]

    max_temperature_values = [
        value
        for value in maximum_temperatures
        if value is not None
    ]

    min_temperature_values = [
        value
        for value in minimum_temperatures
        if value is not None
    ]

    precipitation_values = [
        value
        for value in precipitation
        if value is not None
    ]

    rainfall_values = [
        value
        for value in rainfall
        if value is not None
    ]

    # -----------------------------------------
    # Return structured data
    # -----------------------------------------

    return {
        "status": "live_data",

        "location": location_data["location"],
        "country": location_data["country"],

        "latitude": latitude,
        "longitude": longitude,

        "start_date": start_date,
        "end_date": end_date,

        "dates": dates,

        "temperatures": temperature_values,

        "maximum_temperatures": max_temperature_values,

        "minimum_temperatures": min_temperature_values,

        "precipitation": precipitation_values,

        "rainfall": rainfall_values
    }


def get_last_30_days(location):
    """
    Get historical weather for the last 30 days.
    """

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    return get_historical_weather(
        location,
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )


def get_last_year(location):
    """
    Get historical weather for the previous year.
    """

    current_year = datetime.now().year

    start_date = f"{current_year - 1}-01-01"
    end_date = f"{current_year - 1}-12-31"

    return get_historical_weather(
        location,
        start_date,
        end_date
    )


# =============================================
# TEST
# =============================================

if __name__ == "__main__":

    print("\n======================================")
    print("       CLIMATE DATA TOOL TEST")
    print("======================================")

    location = "Delhi"

    print(f"\nFetching historical weather for {location}...")

    result = get_last_30_days(location)

    print("\nStatus:", result.get("status"))

    if result.get("status") in ["success", "live_data"]:

        print("Location:", result.get("location"))
        print("Country:", result.get("country"))

        print(
            "Period:",
            result.get("start_date"),
            "to",
            result.get("end_date")
        )

        print(
            "Days:",
            len(result.get("dates", []))
        )

        print(
            "Temperature values:",
            len(result.get("temperatures", []))
        )

        print(
            "Rainfall values:",
            len(result.get("rainfall", []))
        )

        print("\nFirst 5 temperatures:")

        for value in result.get("temperatures", [])[:5]:
            print("-", value, "°C")

        print("\nFirst 5 rainfall values:")

        for value in result.get("rainfall", [])[:5]:
            print("-", value, "mm")

    else:

        print(
            "\nERROR:",
            result.get("message")
        )