import os

import pytest

from app.database.mongodb import mongodb
from app.repositories.weather_repository import MongoWeatherRepository


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_REAL_GFS_TESTS") != "1",
    reason="Real GFS integration tests are disabled by default",
)


@pytest.mark.asyncio
async def test_real_gfs_read():
    assert await mongodb.ping() is True

    repository = MongoWeatherRepository(
        mongodb
    )

    result = await repository.get_latest_gfs(
        latitude=20.2961,
        longitude=85.8245,
    )

    print("\n===== REAL GFS DATA =====")
    print(result)

    assert result is not None
    assert result["source"] == "noaa-gfs"

    await mongodb.disconnect()