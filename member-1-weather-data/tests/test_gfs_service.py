import pytest

from app.services.gfs_service import GFSWeatherService


class FakeRepository:
    def __init__(self):
        self.calls = 0

    async def get_latest_gfs(
        self,
        latitude,
        longitude,
    ):
        self.calls += 1

        return {
            "latitude": latitude,
            "longitude": longitude,
            "temperature": 27.5,
            "source": "noaa-gfs",
        }


class FakeCache:
    def __init__(self):
        self.data = {}
        self.get_calls = 0
        self.set_calls = 0

    async def get(self, key):
        self.get_calls += 1
        return self.data.get(key)

    async def set(
        self,
        key,
        value,
        ttl=None,
    ):
        self.set_calls += 1
        self.data[key] = value
        return True


@pytest.mark.asyncio
async def test_gfs_service_cache_miss_reads_repository():

    repository = FakeRepository()
    cache = FakeCache()

    service = GFSWeatherService(
        repository=repository,
        cache=cache,
    )

    result = await service.get_latest(
        latitude=20.2961,
        longitude=85.8245,
    )

    assert result["source"] == "noaa-gfs"

    assert repository.calls == 1

    assert cache.get_calls == 1
    assert cache.set_calls == 1


@pytest.mark.asyncio
async def test_gfs_service_cache_hit_avoids_repository():

    repository = FakeRepository()
    cache = FakeCache()

    service = GFSWeatherService(
        repository=repository,
        cache=cache,
    )

    first = await service.get_latest(
        latitude=20.2961,
        longitude=85.8245,
    )

    second = await service.get_latest(
        latitude=20.2961,
        longitude=85.8245,
    )

    assert first == second

    # Repository should only be accessed once.
    assert repository.calls == 1

    # Redis should be checked twice.
    assert cache.get_calls == 2

    # Redis should only be written on the first request.
    assert cache.set_calls == 1