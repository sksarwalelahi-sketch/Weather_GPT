from datetime import datetime, timezone

import pytest

from app.cache.redis_cache import RedisWeatherCache
from app.database.mongodb import MongoDB
from app.ingestion.imd_ingestion import IMDIngestion
from app.repositories.weather_repository import MongoWeatherRepository


class FakeIMDClient:
    async def get_weather(self, latitude, longitude):
        return {
            "source": "imd",
            "latitude": latitude,
            "longitude": longitude,
            "data": {
                "timestamp": "2026-09-04T12:00:00Z",
                "temperature": 30.5,
                "relative_humidity": 68,
                "precipitation": 0.8,
                "wind_speed": 14.2,
                "wind_direction": 225,
                "pressure": 1002.4,
                "station_id": "IMD-FULL-PIPELINE",
            },
        }

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_imd_full_pipeline():
    latitude = 20.2961
    longitude = 85.8245

    cache_key = (
        f"weather:imd:"
        f"{latitude:.6f}:"
        f"{longitude:.6f}"
    )

    mongodb = MongoDB()
    await mongodb.connect()

    redis_cache = RedisWeatherCache(
        host="127.0.0.1",
        port=6379,
        db=0,
    )

    repository = MongoWeatherRepository(mongodb)

    ingestion = IMDIngestion(
        client=FakeIMDClient(),
        repository=repository,
        cache=redis_cache,
    )

    collection = mongodb.get_database()[
        repository.IMD_COLLECTION
    ]

    try:
        # Remove previous test data.
        await collection.delete_many(
            {
                "station_id": "IMD-FULL-PIPELINE"
            }
        )

        await redis_cache.delete(cache_key)

        # -------------------------------------------------
        # 1. IMD → Normalize → MongoDB + Redis
        # -------------------------------------------------
        weather = await ingestion.ingest_weather(
            latitude=latitude,
            longitude=longitude,
        )

        assert weather.source == "imd"
        assert weather.latitude == latitude
        assert weather.longitude == longitude
        assert weather.temperature == 30.5
        assert weather.relative_humidity == 68

        # -------------------------------------------------
        # 2. Verify exact MongoDB document created by test
        # -------------------------------------------------
        saved_document = await collection.find_one(
            {
                "station_id": "IMD-FULL-PIPELINE"
            }
        )

        assert saved_document is not None
        assert saved_document["source"] == "imd"
        assert saved_document["latitude"] == latitude
        assert saved_document["longitude"] == longitude
        assert saved_document["temperature"] == 30.5
        assert saved_document["relative_humidity"] == 68
        assert saved_document["station_id"] == "IMD-FULL-PIPELINE"

        # -------------------------------------------------
        # 3. Verify Redis
        # -------------------------------------------------
        cached = await redis_cache.get(cache_key)

        assert cached is not None
        assert cached["source"] == "imd"
        assert cached["latitude"] == latitude
        assert cached["longitude"] == longitude
        assert cached["temperature"] == 30.5
        assert cached["relative_humidity"] == 68

        print("\nIMD FULL PIPELINE SUCCESS")
        print(
            "IMD → Normalize → MongoDB Atlas + Memurai Redis"
        )

    finally:
        # MongoDB cleanup.
        await collection.delete_many(
            {
                "station_id": "IMD-FULL-PIPELINE"
            }
        )

        # Redis cleanup.
        await redis_cache.delete(cache_key)

        await redis_cache.close()
        await mongodb.disconnect()