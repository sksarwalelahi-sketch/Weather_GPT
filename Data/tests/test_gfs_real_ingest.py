import os

import pytest

from app.database.mongodb import mongodb
from app.gfs.ingestion import GFSIngestion
from app.repositories.weather_repository import MongoWeatherRepository


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_REAL_GFS_TESTS") != "1",
    reason="Real GFS integration tests are disabled by default",
)


@pytest.mark.asyncio
async def test_real_gfs_ingestion_to_mongodb():
    assert await mongodb.ping() is True

    repository = MongoWeatherRepository(
        mongodb
    )

    ingestion = GFSIngestion(
        repository=repository
    )

    try:
        result = await ingestion.ingest_grib2(
            file_path="data/gfs_f003_test.grib2",
            latitude=20.2961,
            longitude=85.8245,
        )

        print("\n===== INGESTED GFS DATA =====")
        print(result)

        assert result is not None
        assert result.source == "noaa-gfs"
        assert result.temperature is not None

        stored = await repository.get_latest_gfs(
            latitude=20.2961,
            longitude=85.8245,
        )

        print("\n===== GFS DATA FROM MONGODB =====")
        print(stored)

        assert stored is not None
        assert stored["source"] == "noaa-gfs"

    finally:
        await ingestion.close()
        await mongodb.disconnect()