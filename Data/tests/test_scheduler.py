from unittest.mock import patch

import pytest

from app.scheduler.weather_scheduler import (
    WeatherScheduler,
)


class FakeWeatherIngestion:
    def __init__(self):
        self.calls = []
        self.closed = False

    async def ingest_current(
        self,
        latitude,
        longitude,
    ):
        self.calls.append(
            (latitude, longitude)
        )

        return {
            "source": "open-meteo",
        }

    async def close(self):
        self.closed = True


class FakeGFSIngestion:
    def __init__(self):
        self.calls = []
        self.closed = False

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
        self.closed = True


class FakeCycle:
    date = "20260830"
    cycle = 12
    cycle_text = "12"


def create_scheduler():
    return WeatherScheduler(
        ingestion=FakeWeatherIngestion(),
        gfs_ingestion=FakeGFSIngestion(),
        interval_minutes=15,
    )


def test_scheduler_configuration():
    scheduler = create_scheduler()

    assert scheduler.interval_minutes == 15

    assert scheduler.JOB_ID == (
        "weather-current-ingestion"
    )

    assert scheduler.CURRENT_JOB_ID == (
        "weather-current-ingestion"
    )

    assert scheduler.GFS_JOB_ID == (
        "gfs-ingestion"
    )


def test_scheduler_rejects_invalid_interval():
    with pytest.raises(ValueError):
        WeatherScheduler(
            ingestion=FakeWeatherIngestion(),
            gfs_ingestion=FakeGFSIngestion(),
            interval_minutes=0,
        )


def test_add_current_weather_job():
    scheduler = create_scheduler()

    scheduler.add_current_weather_job(
        latitude=20.2961,
        longitude=85.8245,
    )

    jobs = scheduler.scheduler.get_jobs()

    assert len(jobs) == 1
    assert jobs[0].id == (
        scheduler.CURRENT_JOB_ID
    )


def test_add_gfs_job():
    scheduler = create_scheduler()

    scheduler.add_gfs_job(
        latitude=20.2961,
        longitude=85.8245,
    )

    jobs = scheduler.scheduler.get_jobs()

    assert len(jobs) == 1
    assert jobs[0].id == (
        scheduler.GFS_JOB_ID
    )


@pytest.mark.asyncio
async def test_run_current_ingestion():
    ingestion = FakeWeatherIngestion()

    scheduler = WeatherScheduler(
        ingestion=ingestion,
        gfs_ingestion=FakeGFSIngestion(),
    )

    result = await scheduler.run_current_ingestion(
        latitude=20.2961,
        longitude=85.8245,
    )

    assert result["source"] == "open-meteo"

    assert ingestion.calls == [
        (20.2961, 85.8245)
    ]


@pytest.mark.asyncio
async def test_run_gfs_ingestion():
    gfs_ingestion = FakeGFSIngestion()

    scheduler = WeatherScheduler(
        ingestion=FakeWeatherIngestion(),
        gfs_ingestion=gfs_ingestion,
    )

    result = await scheduler.run_gfs_ingestion(
        url="https://example.com/gfs.grib2",
        output_path="data/gfs.grib2",
        latitude=20.2961,
        longitude=85.8245,
    )

    assert result["source"] == "noaa-gfs"

    assert gfs_ingestion.calls == [
        {
            "url": "https://example.com/gfs.grib2",
            "output_path": "data/gfs.grib2",
            "latitude": 20.2961,
            "longitude": 85.8245,
        }
    ]


@pytest.mark.asyncio
async def test_automatic_gfs_ingestion():
    gfs_ingestion = FakeGFSIngestion()

    scheduler = WeatherScheduler(
        ingestion=FakeWeatherIngestion(),
        gfs_ingestion=gfs_ingestion,
    )

    with patch(
        "app.scheduler.weather_scheduler.GFSCycleResolver.resolve",
        return_value=FakeCycle(),
    ), patch(
        "app.scheduler.weather_scheduler.GFSCycleResolver.build_url",
        return_value=(
            "https://nomads.example/gfs.grib2"
        ),
    ):
        result = (
            await scheduler.run_automatic_gfs_ingestion(
                latitude=20.2961,
                longitude=85.8245,
                output_directory="test-data/gfs",
                forecast_hour=0,
            )
        )

    assert result["source"] == "noaa-gfs"

    assert len(
        gfs_ingestion.calls
    ) == 1

    call = gfs_ingestion.calls[0]

    assert call["url"] == (
        "https://nomads.example/gfs.grib2"
    )

    assert call["latitude"] == 20.2961
    assert call["longitude"] == 85.8245

    assert call["output_path"].endswith(
        "gfs.20260830.12z.f000.grib2"
    )


@pytest.mark.asyncio
async def test_duplicate_gfs_cycle_is_skipped():
    gfs_ingestion = FakeGFSIngestion()

    scheduler = WeatherScheduler(
        ingestion=FakeWeatherIngestion(),
        gfs_ingestion=gfs_ingestion,
    )

    with patch(
        "app.scheduler.weather_scheduler.GFSCycleResolver.resolve",
        return_value=FakeCycle(),
    ), patch(
        "app.scheduler.weather_scheduler.GFSCycleResolver.build_url",
        return_value=(
            "https://nomads.example/gfs.grib2"
        ),
    ):
        first = (
            await scheduler.run_automatic_gfs_ingestion(
                latitude=20.2961,
                longitude=85.8245,
                output_directory="test-data/gfs",
            )
        )

        second = (
            await scheduler.run_automatic_gfs_ingestion(
                latitude=20.2961,
                longitude=85.8245,
                output_directory="test-data/gfs",
            )
        )

    assert first["source"] == "noaa-gfs"
    assert second is None

    assert len(
        gfs_ingestion.calls
    ) == 1


@pytest.mark.asyncio
async def test_new_gfs_cycle_is_processed():
    gfs_ingestion = FakeGFSIngestion()

    scheduler = WeatherScheduler(
        ingestion=FakeWeatherIngestion(),
        gfs_ingestion=gfs_ingestion,
    )

    first_cycle = FakeCycle()

    second_cycle = FakeCycle()

    second_cycle.date = "20260830"
    second_cycle.cycle = 18
    second_cycle.cycle_text = "18"

    with patch(
        "app.scheduler.weather_scheduler.GFSCycleResolver.resolve",
        side_effect=[
            first_cycle,
            second_cycle,
        ],
    ), patch(
        "app.scheduler.weather_scheduler.GFSCycleResolver.build_url",
        side_effect=[
            "https://example.com/gfs12.grib2",
            "https://example.com/gfs18.grib2",
        ],
    ):
        first = (
            await scheduler.run_automatic_gfs_ingestion(
                latitude=20.2961,
                longitude=85.8245,
            )
        )

        second = (
            await scheduler.run_automatic_gfs_ingestion(
                latitude=20.2961,
                longitude=85.8245,
            )
        )

    assert first["source"] == "noaa-gfs"
    assert second["source"] == "noaa-gfs"

    assert len(
        gfs_ingestion.calls
    ) == 2


def test_both_jobs_can_be_registered():
    scheduler = create_scheduler()

    scheduler.add_current_weather_job(
        latitude=20.2961,
        longitude=85.8245,
    )

    scheduler.add_gfs_job(
        latitude=20.2961,
        longitude=85.8245,
    )

    jobs = scheduler.scheduler.get_jobs()

    assert len(jobs) == 2

    job_ids = {
        job.id
        for job in jobs
    }

    assert scheduler.CURRENT_JOB_ID in job_ids
    assert scheduler.GFS_JOB_ID in job_ids


@pytest.mark.asyncio
async def test_close_closes_both_ingestion_services():
    ingestion = FakeWeatherIngestion()
    gfs_ingestion = FakeGFSIngestion()

    scheduler = WeatherScheduler(
        ingestion=ingestion,
        gfs_ingestion=gfs_ingestion,
    )

    await scheduler.close()

    assert ingestion.closed is True
    assert gfs_ingestion.closed is True