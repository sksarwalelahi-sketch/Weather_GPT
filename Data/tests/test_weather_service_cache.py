import pytest

from app.services.weather_service import WeatherService


class FakeWeather:
    def model_dump(self, mode="json"):
        return {
            "latitude": 20.2961,
            "longitude": 85.8245,
            "temperature": 27.5,
            "relative_humidity": 80.0,
            "apparent_temperature": 30.0,
            "precipitation": 0.0,
            "rain": 0.0,
            "weather_code": 3,
            "cloud_cover": 50.0,
            "surface_pressure": 997.0,
            "wind_speed": 8.0,
            "wind_direction": 250.0,
            "wind_gusts": 12.0,
            "observed_at": "2026-09-02T00:00:00",
            "source": "open-meteo",
        }


class FakeClient:
    def __init__(self):
        self.calls = 0

    async def get_weather(
        self,
        latitude,
        longitude,
    ):
        self.calls += 1

        from app.models.weather import (
            CurrentWeather,
            OpenMeteoResponse,
        )
        from datetime import datetime

        return OpenMeteoResponse(
            latitude=latitude,
            longitude=longitude,
            generationtime_ms=0.1,
            utc_offset_seconds=0,
            timezone="GMT",
            timezone_abbreviation="GMT",
            elevation=44.0,
            current_units={
                "temperature_2m": "°C",
                "relative_humidity_2m": "%",
                "apparent_temperature": "°C",
                "precipitation": "mm",
                "rain": "mm",
                "weather_code": "wmo code",
                "cloud_cover": "%",
                "surface_pressure": "hPa",
                "wind_speed_10m": "km/h",
                "wind_direction_10m": "°",
                "wind_gusts_10m": "km/h",
            },
            current=CurrentWeather(
                time=datetime(2026, 9, 2, 0, 0),
                temperature_2m=27.5,
                relative_humidity_2m=80.0,
                apparent_temperature=30.0,
                precipitation=0.0,
                rain=0.0,
                weather_code=3,
                cloud_cover=50.0,
                surface_pressure=997.0,
                wind_speed_10m=8.0,
                wind_direction_10m=250.0,
                wind_gusts_10m=12.0,
            ),
        )

    async def close(self):
        pass


class FakeRepository:
    def __init__(self):
        self.current = []

    async def save_current(self, weather):
        self.current.append(weather)
        return "test-id"


class FakeCache:
    CURRENT_TTL = 300

    def __init__(self):
        self.storage = {}
        self.get_calls = 0
        self.set_calls = 0

    @staticmethod
    def current_key(latitude, longitude):
        return (
            f"weather:current:"
            f"{latitude:.6f}:"
            f"{longitude:.6f}"
        )

    async def get(self, key):
        self.get_calls += 1
        return self.storage.get(key)

    async def set(self, key, value, ttl=None):
        self.set_calls += 1
        self.storage[key] = value
        return True


@pytest.mark.asyncio
async def test_cache_hit_avoids_external_weather_request():
    client = FakeClient()
    repository = FakeRepository()
    cache = FakeCache()

    service = WeatherService(
        client=client,
        repository=repository,
        cache=cache,
    )

    first = await service.get_current_weather(
        latitude=20.2961,
        longitude=85.8245,
    )

    assert client.calls == 1
    assert len(repository.current) == 1
    assert cache.get_calls == 1
    assert cache.set_calls == 1

    second = await service.get_current_weather(
        latitude=20.2961,
        longitude=85.8245,
    )

    assert client.calls == 1
    assert len(repository.current) == 1
    assert cache.get_calls == 2
    assert cache.set_calls == 1

    assert second == first

    await service.close()