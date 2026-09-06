from datetime import datetime, timezone

import pytest

from app.ingestion.imd_ingestion import IMDIngestion


class FakeIMDClient:
    async def get_weather(self, latitude, longitude):
        return {
            "source": "imd",
            "latitude": latitude,
            "longitude": longitude,
            "data": {
                "timestamp": "2026-09-04T12:00:00Z",
                "temperature": 29.5,
                "relative_humidity": 72,
                "precipitation": 1.2,
                "wind_speed": 12.5,
                "wind_direction": 240,
                "pressure": 999.5,
                "station_id": "IMD-TEST-01",
            },
        }

    async def close(self):
        pass


class FakeRepository:
    def __init__(self):
        self.saved = []

    async def save_imd_weather(self, weather):
        self.saved.append(weather)
        return "fake-imd-id"


class FakeCache:
    def __init__(self):
        self.values = {}

    async def set(self, key, value, ttl=None):
        self.values[key] = {
            "value": value,
            "ttl": ttl,
        }


@pytest.mark.asyncio
async def test_imd_ingestion_normalizes_weather():
    client = FakeIMDClient()

    ingestion = IMDIngestion(client=client)

    weather = await ingestion.ingest_weather(
        latitude=20.2961,
        longitude=85.8245,
    )

    assert weather.source == "imd"
    assert weather.latitude == 20.2961
    assert weather.longitude == 85.8245
    assert weather.temperature == 29.5
    assert weather.relative_humidity == 72
    assert weather.precipitation == 1.2


@pytest.mark.asyncio
async def test_imd_ingestion_preserves_coordinates():
    class CoordinateMissingClient:
        async def get_weather(self, latitude, longitude):
            return {
                "data": {
                    "timestamp": "2026-09-04T12:00:00Z",
                    "temperature": 28.0,
                }
            }

        async def close(self):
            pass

    ingestion = IMDIngestion(
        client=CoordinateMissingClient()
    )

    weather = await ingestion.ingest_weather(
        latitude=20.2961,
        longitude=85.8245,
    )

    assert weather.latitude == 20.2961
    assert weather.longitude == 85.8245


@pytest.mark.asyncio
async def test_imd_ingestion_saves_to_repository():
    client = FakeIMDClient()
    repository = FakeRepository()

    ingestion = IMDIngestion(
        client=client,
        repository=repository,
    )

    weather = await ingestion.ingest_weather(
        latitude=20.2961,
        longitude=85.8245,
    )

    assert len(repository.saved) == 1
    assert repository.saved[0].source == "imd"
    assert repository.saved[0].temperature == 29.5


@pytest.mark.asyncio
async def test_imd_ingestion_caches_weather():
    client = FakeIMDClient()
    cache = FakeCache()

    ingestion = IMDIngestion(
        client=client,
        cache=cache,
    )

    weather = await ingestion.ingest_weather(
        latitude=20.2961,
        longitude=85.8245,
    )

    expected_key = "weather:imd:20.296100:85.824500"

    assert expected_key in cache.values
    assert cache.values[expected_key]["value"]["source"] == "imd"
    assert cache.values[expected_key]["value"]["temperature"] == 29.5
    assert cache.values[expected_key]["ttl"] == 300


@pytest.mark.asyncio
async def test_imd_ingestion_saves_and_caches():
    client = FakeIMDClient()
    repository = FakeRepository()
    cache = FakeCache()

    ingestion = IMDIngestion(
        client=client,
        repository=repository,
        cache=cache,
    )

    weather = await ingestion.ingest_weather(
        latitude=20.2961,
        longitude=85.8245,
    )

    assert weather.source == "imd"

    assert len(repository.saved) == 1

    expected_key = "weather:imd:20.296100:85.824500"
    assert expected_key in cache.values


@pytest.mark.asyncio
async def test_imd_client_requires_configured_endpoint():
    from app.ingestion.imd_ingestion import IMDClient

    client = IMDClient()

    with pytest.raises(RuntimeError, match="IMD data source is not configured"):
        await client.get_weather(
            latitude=20.2961,
            longitude=85.8245,
        )

    await client.close()