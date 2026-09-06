import pytest

from app.ingestion.satellite_ingestion import (
    SatelliteWeatherIngestion,
)


class FakeRepository:
    def __init__(self):
        self.saved = []

    async def save_satellite_weather(
        self,
        weather,
    ):
        self.saved.append(weather)
        return "test-id"


class FakeCache:
    def __init__(self):
        self.values = {}

    async def set(
        self,
        key,
        value,
        ttl=None,
    ):
        self.values[key] = {
            "value": value,
            "ttl": ttl,
        }

        return True


@pytest.mark.asyncio
async def test_satellite_ingestion_pipeline():
    repository = FakeRepository()
    cache = FakeCache()

    ingestion = SatelliteWeatherIngestion(
        repository=repository,
        cache=cache,
    )

    payload = {
        "data": {
            "lat": 20.2961,
            "lon": 85.8245,
            "time": "2026-09-04T10:00:00Z",
            "cloud": 72.0,
            "brightness_temp": 248.3,
            "rainfall": 0.8,
            "solar": 510.0,
        },
        "product": "INSAT-test",
    }

    result = await ingestion.ingest(
        payload
    )

    assert result["latitude"] == 20.2961
    assert result["longitude"] == 85.8245
    assert result["cloud_cover"] == 72.0
    assert result["brightness_temperature"] == 248.3
    assert result["rainfall_estimate"] == 0.8
    assert result["solar_radiation"] == 510.0

    assert len(repository.saved) == 1
    assert len(cache.values) == 1


@pytest.mark.asyncio
async def test_satellite_ingestion_rejects_invalid_payload():
    ingestion = SatelliteWeatherIngestion()

    with pytest.raises(TypeError):
        await ingestion.ingest(
            "invalid"
        )