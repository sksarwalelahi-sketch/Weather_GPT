import pytest

from app.database.mongodb import MongoDB
from app.repositories.weather_repository import (
    MongoWeatherRepository,
)


def test_mongodb_configuration():
    database = MongoDB(
        uri="mongodb://localhost:27017",
        database_name="weathergpt_test",
    )

    assert database.uri == "mongodb://localhost:27017"
    assert database.database_name == "weathergpt_test"


@pytest.mark.asyncio
async def test_mongodb_connect_disconnect():
    database = MongoDB(
        uri="mongodb://localhost:27017",
        database_name="weathergpt_test",
    )

    await database.connect()

    assert database.client is not None
    assert database.database is not None

    await database.disconnect()

    assert database.client is None
    assert database.database is None


def test_repository_collections():
    database = MongoDB(
        database_name="weathergpt_test",
    )

    repository = MongoWeatherRepository(database)

    assert repository.CURRENT_COLLECTION == "current_weather"
    assert repository.FORECAST_COLLECTION == "weather_forecasts"
    assert repository.HISTORICAL_COLLECTION == "historical_weather"