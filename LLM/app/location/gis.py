"""Geocoding, reverse geocoding, and coordinate validation helpers."""

import requests


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
REVERSE_GEOCODING_URL = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = "WeatherGPT-AI/1.0"


def validate_coordinates(
    latitude: float,
    longitude: float,
) -> None:
    """Validate geographic coordinates used by WeatherGPT services."""

    if not -90 <= latitude <= 90:
        raise ValueError("latitude must be between -90 and 90")

    if not -180 <= longitude <= 180:
        raise ValueError("longitude must be between -180 and 180")


def search_locations(
    query: str,
    count: int = 5,
) -> list[dict]:
    """Find cities, towns, villages, and rural settlements.

    Open-Meteo is fast for common place names, while Nominatim provides
    broader OpenStreetMap coverage for small localities that are not included
    in the Open-Meteo database.
    """

    if not query or not query.strip():
        raise ValueError("location query is required")

    normalized_query = query.strip()
    locations: list[dict] = []

    try:
        response = requests.get(
            GEOCODING_URL,
            params={
                "name": normalized_query,
                "count": count,
                "language": "en",
                "format": "json",
            },
            timeout=10,
        )
        response.raise_for_status()

        for place in response.json().get("results", []):
            locations.append(
                {
                    "name": place.get("name"),
                    "latitude": place.get("latitude"),
                    "longitude": place.get("longitude"),
                    "country": place.get("country"),
                    "country_code": place.get("country_code"),
                    "admin1": place.get("admin1"),
                    "admin2": place.get("admin2"),
                    "timezone": place.get("timezone"),
                }
            )
    except requests.RequestException:
        # Nominatim below is the broader provider and can still resolve the
        # query when Open-Meteo is temporarily unavailable.
        locations = []

    if len(locations) < count:
        try:
            response = requests.get(
                REVERSE_GEOCODING_URL.replace("/reverse", "/search"),
                params={
                    "q": normalized_query,
                    "format": "jsonv2",
                    "addressdetails": 1,
                    "limit": count,
                    "dedupe": 1,
                    "accept-language": "en",
                },
                headers={"User-Agent": USER_AGENT},
                timeout=10,
            )
            response.raise_for_status()

            for place in response.json():
                address = place.get("address", {})
                locations.append(
                    {
                        "name": (
                            place.get("name")
                            or address.get("village")
                            or address.get("town")
                            or address.get("municipality")
                            or address.get("county")
                        ),
                        "display_name": place.get("display_name"),
                        "latitude": float(place["lat"]),
                        "longitude": float(place["lon"]),
                        "country": address.get("country"),
                        "country_code": address.get("country_code"),
                        "admin1": address.get("state"),
                        "admin2": address.get("county"),
                        "timezone": None,
                    }
                )
        except (requests.RequestException, KeyError, TypeError, ValueError):
            # Preserve successful Open-Meteo results if the optional broader
            # lookup is unavailable.
            pass

    unique_locations: list[dict] = []
    seen_coordinates: set[tuple[float, float]] = set()
    for location in locations:
        try:
            coordinate_key = (
                round(float(location["latitude"]), 4),
                round(float(location["longitude"]), 4),
            )
        except (KeyError, TypeError, ValueError):
            continue
        if coordinate_key in seen_coordinates:
            continue
        seen_coordinates.add(coordinate_key)
        unique_locations.append(location)
        if len(unique_locations) >= count:
            break

    return unique_locations


def get_coordinates(location: str) -> dict:
    """Resolve one location name into the coordinates used by weather tools."""

    locations = search_locations(location, count=1)

    if not locations:
        raise ValueError(f"Location not found: {location}")

    return locations[0]


def reverse_geocode(
    latitude: float,
    longitude: float,
) -> dict:
    """Resolve coordinates to a human-readable location for map consumers."""

    validate_coordinates(latitude, longitude)

    response = requests.get(
        REVERSE_GEOCODING_URL,
        params={
            "lat": latitude,
            "lon": longitude,
            "format": "jsonv2",
            "zoom": 10,
        },
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )

    response.raise_for_status()

    place = response.json()
    address = place.get("address", {})

    return {
        "name": place.get("name") or place.get("display_name"),
        "display_name": place.get("display_name"),
        "latitude": float(place.get("lat", latitude)),
        "longitude": float(place.get("lon", longitude)),
        "country": address.get("country"),
        "country_code": address.get("country_code"),
        "admin1": address.get("state"),
    }
