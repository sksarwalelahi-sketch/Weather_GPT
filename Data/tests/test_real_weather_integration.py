import pytest

from app.cache.redis_cache import RedisWeatherCache
from app.database.mongodb import mongodb
from app.repositories.weather_repository import MongoWeatherRepository
from app.services.weather_service import WeatherService


@pytest.mark.asyncio
async def test_real_weather_stack():
    latitude = 20.2961
    longitude = 85.8245

    cache = RedisWeatherCache()

    # Connect/check MongoDB Atlas.
    assert await mongodb.ping() is True

    repository = MongoWeatherRepository(
        mongodb
    )

    service = WeatherService(
        repository=repository,
        cache=cache,
    )

    cache_key = cache.current_key(
        latitude,
        longitude,
    )

    try:
        # Start clean for this location.
        await cache.delete(cache_key)

        print("\n===== FIRST REQUEST =====")

        first = await service.get_current_weather(
            latitude=latitude,
            longitude=longitude,
        )

        print(first)

        assert first is not None
        assert first.source == "open-meteo"

        print("\n===== REDIS AFTER FIRST REQUEST =====")

        cached = await cache.get(cache_key)

        print(cached)

        assert cached is not None

        print("\n===== SECOND REQUEST =====")

        second = await service.get_current_weather(
            latitude=latitude,
            longitude=longitude,
        )

        print(second)

        assert second is not None
        assert second.source == "open-meteo"

        assert second.temperature == first.temperature

        print("\n===== MONGODB =====")
        print("MongoDB Atlas: CONNECTED")

    finally:
        await cache.delete(cache_key)
        await service.close()
        await cache.close()
        await mongodb.disconnect()