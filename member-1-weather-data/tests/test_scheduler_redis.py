import pytest

from app.scheduler.weather_scheduler import WeatherScheduler


class FakeRedisCache:
    def __init__(self):
        self.data = {}

    async def get(self, key):
        return self.data.get(key)

    async def set(self, key, value, ttl=None):
        self.data[key] = value
        return True

    async def close(self):
        pass


class FakeWeatherIngestion:
    async def ingest_current(
        self,
        latitude,
        longitude,
    ):
        return {
            "source": "open-meteo",
        }

    async def close(self):
        pass


class FakeGFSIngestion:
    def __init__(self):
        self.calls = []

    async def ingest_remote(
        self,
        url,
        output_path,
        latitude,
        longitude,
    ):
        self.calls.append(
            {
                "url": url,
                "output_path": output_path,
                "latitude": latitude,
                "longitude": longitude,
            }
        )

        return {
            "source": "noaa-gfs",
        }

    async def close(self):
        pass


class FakeCycle:
    date = "20260903"
    cycle = 12
    cycle_text = "12"


@pytest.mark.asyncio
async def test_gfs_cycle_persists_across_scheduler_restart(
    monkeypatch,
):
    redis = FakeRedisCache()

    first_gfs = FakeGFSIngestion()

    first_scheduler = WeatherScheduler(
        ingestion=FakeWeatherIngestion(),
        gfs_ingestion=first_gfs,
        redis_cache=redis,
    )

    monkeypatch.setattr(
        "app.scheduler.weather_scheduler.GFSCycleResolver.resolve",
        lambda: FakeCycle(),
    )

    monkeypatch.setattr(
        "app.scheduler.weather_scheduler.GFSCycleResolver.build_url",
        lambda forecast_hour=0: (
            "https://example.com/gfs.grib2"
        ),
    )

    first_result = (
        await first_scheduler.run_automatic_gfs_ingestion(
            latitude=20.2961,
            longitude=85.8245,
        )
    )

    assert first_result["source"] == "noaa-gfs"
    assert len(first_gfs.calls) == 1

    # Simulate a fresh scheduler after application restart.
    second_gfs = FakeGFSIngestion()

    second_scheduler = WeatherScheduler(
        ingestion=FakeWeatherIngestion(),
        gfs_ingestion=second_gfs,
        redis_cache=redis,
    )

    second_result = (
        await second_scheduler.run_automatic_gfs_ingestion(
            latitude=20.2961,
            longitude=85.8245,
        )
    )

    assert second_result is None
    assert len(second_gfs.calls) == 0
    