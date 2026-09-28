from datetime import datetime, timezone

import pytest

from app.database.mongodb import MongoDB
from app.models.imd_weather import IMDWeather
from app.repositories.weather_repository import MongoWeatherRepository


@pytest.mark.asyncio
async def test_save_and_read_imd_weather():
    mongodb = MongoDB()
    await mongodb.connect()

    try:
        repository = MongoWeatherRepository(mongodb)

        weather = IMDWeather(
            latitude=20.2961,
            longitude=85.8245,
            timestamp=datetime.now(timezone.utc),
            temperature=29.5,
            relative_humidity=72,
            precipitation=1.2,
            wind_speed=12.5,
            wind_direction=240,
            pressure=999.5,
            source="imd",
            station_id="IMD-TEST-REPOSITORY",
        )

        document_id = await repository.save_imd_weather(
            weather
        )

        assert document_id is not None

        latest = await repository.get_latest_imd(
            latitude=20.2961,
            longitude=85.8245,
        )

        assert latest is not None
        assert latest["source"] == "imd"
        assert latest["latitude"] == 20.2961
        assert latest["longitude"] == 85.8245
        assert latest["temperature"] == 29.5
        assert latest["station_id"] == "IMD-TEST-REPOSITORY"

        collection = mongodb.get_database()[
            repository.IMD_COLLECTION
        ]

        await collection.delete_one(
            {"_id": document_id}
        )

    finally:
        await mongodb.disconnect()