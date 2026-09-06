from datetime import datetime, timezone

import pytest

from app.database.mongodb import MongoDB
from app.models.imd_weather import IMDWeather
from app.repositories.weather_repository import MongoWeatherRepository


@pytest.mark.asyncio
async def test_get_latest_imd_returns_newest_timestamp():
    mongodb = MongoDB()
    await mongodb.connect()

    repository = MongoWeatherRepository(mongodb)

    collection = mongodb.get_database()[
        repository.IMD_COLLECTION
    ]

    latitude = 20.2961
    longitude = 85.8245

    try:
        await collection.delete_many(
            {
                "station_id": "IMD-LATEST-TEST"
            }
        )

        older = IMDWeather(
            latitude=latitude,
            longitude=longitude,
            timestamp=datetime(
                2026,
                9,
                4,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            temperature=25.0,
            source="imd",
            station_id="IMD-LATEST-TEST",
        )

        newer = IMDWeather(
            latitude=latitude,
            longitude=longitude,
            timestamp=datetime(
                2026,
                9,
                4,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            temperature=30.5,
            source="imd",
            station_id="IMD-LATEST-TEST",
        )

        await repository.save_imd_weather(older)
        await repository.save_imd_weather(newer)

        latest = await collection.find_one(
    {
        "station_id": "IMD-LATEST-TEST",
    },
    sort=[
        ("timestamp", -1),
    ],
)

        assert latest is not None
        assert latest["temperature"] == 30.5
        assert latest["timestamp"].replace("Z", "+00:00") == newer.timestamp.isoformat()

    finally:
        await collection.delete_many(
            {
                "station_id": "IMD-LATEST-TEST"
            }
        )

        await mongodb.disconnect()