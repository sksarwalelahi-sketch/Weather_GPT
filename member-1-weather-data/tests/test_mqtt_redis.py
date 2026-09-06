import asyncio

from app.core.dependencies import redis_cache


async def main():
    key = "weather:mqtt:20.296100:85.824500"

    value = {
        "latitude": 20.2961,
        "longitude": 85.8245,
        "temperature": 29.1,
        "relative_humidity": 76.0,
        "wind_speed": 10.5,
        "wind_direction": 235.0,
        "precipitation": 0.1,
        "source": "mqtt-test",
    }

    print("Redis ping:", await redis_cache.ping())

    await redis_cache.set(
        key,
        value,
        ttl=300,
    )

    cached = await redis_cache.get(key)

    print("Cached MQTT weather:")
    print(cached)

    await redis_cache.delete(key)

    print(
        "Cache exists after delete:",
        await redis_cache.exists(key),
    )


if __name__ == "__main__":
    asyncio.run(main())