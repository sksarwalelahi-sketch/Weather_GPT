from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.cache.redis_cache import RedisWeatherCache
from app.gfs.client import GFSClient
from app.gfs.cycle import GFSCycleResolver
from app.gfs.ingestion import GFSIngestion
from app.ingestion.weather_ingestion import WeatherIngestion
from app.era5.ingestion import ERA5IngestionService
from app.core.dependencies import weather_repository
from app.workers.ingestion_workers import IngestionWorkerPool


@dataclass(frozen=True)
class WeatherLocation:
    latitude: float
    longitude: float


class WeatherScheduler:
    """
    Schedules periodic meteorological data ingestion.

    Open-Meteo:
        scheduler -> WeatherIngestion

    GFS:
        scheduler
            -> GFSCycleResolver
            -> GFS URL
            -> GFSIngestion

    ERA5:
        scheduler
            -> ERA5IngestionService
            -> normalization
            -> MongoDB

    Persistent GFS cycle tracking is optional and is provided
    through Redis by the application.
    """

    JOB_ID = "weather-current-ingestion"
    CURRENT_JOB_ID = JOB_ID
    GFS_JOB_ID = "gfs-ingestion"
    ERA5_JOB_ID = "era5-ingestion"

    GFS_CYCLE_CACHE_KEY = (
        "weather:scheduler:last-gfs-cycle"
    )

    GFS_CYCLE_CACHE_TTL = 172800

    ERA5_INTERVAL_HOURS = 6

    def __init__(
        self,
        ingestion: WeatherIngestion | None = None,
        gfs_ingestion: GFSIngestion | None = None,
        redis_cache: RedisWeatherCache | None = None,
        interval_minutes: int = 15,
        worker_pool: IngestionWorkerPool | None = None,
    ):
        if interval_minutes < 1:
            raise ValueError(
                "interval_minutes must be at least 1"
            )

        self.ingestion = (
            ingestion or WeatherIngestion()
        )

        self.gfs_ingestion = (
            gfs_ingestion or GFSIngestion()
        )

        self.redis_cache = redis_cache
        self.worker_pool = worker_pool

        self.interval_minutes = interval_minutes
        self.scheduler = AsyncIOScheduler()

        self._last_gfs_cycles = {}

    # ---------------------------------------------------------
    # CURRENT WEATHER
    # ---------------------------------------------------------

    async def run_current_ingestion(
        self,
        latitude: float,
        longitude: float,
    ):
        async def work():
            return await self.ingestion.ingest_current(
                latitude=latitude,
                longitude=longitude,
            )

        if self.worker_pool is None:
            return await work()
        return await self.worker_pool.submit("current-weather", work)

    # ---------------------------------------------------------
    # GFS
    # ---------------------------------------------------------

    async def run_gfs_ingestion(
        self,
        url: str,
        output_path: str,
        latitude: float,
        longitude: float,
    ):
        async def work():
            return await self.gfs_ingestion.ingest_remote(
                url=url,
                output_path=output_path,
                latitude=latitude,
                longitude=longitude,
            )

        if self.worker_pool is None:
            return await work()
        return await self.worker_pool.submit("gfs", work)

    def _gfs_cycle_cache_key(
        self,
        latitude: float,
        longitude: float,
    ) -> str:
        return (
            f"{self.GFS_CYCLE_CACHE_KEY}:"
            f"{latitude:.6f}:{longitude:.6f}"
        )

    async def _get_last_gfs_cycle(
        self,
        latitude: float,
        longitude: float,
    ):
        if self.redis_cache is None:
            return None

        try:
            return await self.redis_cache.get(
                self._gfs_cycle_cache_key(
                    latitude,
                    longitude,
                )
            )
        except Exception:
            return None

    async def _save_last_gfs_cycle(
        self,
        cycle_key,
        latitude: float,
        longitude: float,
    ):
        if self.redis_cache is None:
            return

        try:
            await self.redis_cache.set(
                self._gfs_cycle_cache_key(
                    latitude,
                    longitude,
                ),
                cycle_key,
                ttl=self.GFS_CYCLE_CACHE_TTL,
            )
        except Exception:
            pass

    async def run_automatic_gfs_ingestion(
        self,
        latitude: float,
        longitude: float,
        output_directory: str = "data/gfs",
        forecast_hour: int = 0,
    ):
        cycle = GFSCycleResolver.resolve_available()

        cycle_key = (
            cycle.date,
            cycle.cycle,
            forecast_hour,
        )

        # In-memory protection.
        location_key = (latitude, longitude)
        if (
            cycle_key
            == self._last_gfs_cycles.get(location_key)
        ):
            return None

        # Persistent protection through Redis.
        persisted_cycle = (
            await self._get_last_gfs_cycle(
                latitude,
                longitude,
            )
        )

        expected_persisted_cycle = {
            "date": cycle.date,
            "cycle": cycle.cycle,
            "forecast_hour": forecast_hour,
        }

        if persisted_cycle == expected_persisted_cycle:
            self._last_gfs_cycles[location_key] = (
                cycle_key
            )
            return None

        top_latitude = min(90.0, latitude + 2.0)
        bottom_latitude = max(-90.0, latitude - 2.0)
        left_longitude = max(-180.0, longitude - 2.0)
        right_longitude = min(180.0, longitude + 2.0)
        url = GFSClient.build_url(
            date=cycle.date,
            cycle=cycle.cycle,
            forecast_hour=forecast_hour,
            variables=["TMP", "RH", "UGRD", "VGRD", "PRES"],
            levels=[
                "2_m_above_ground",
                "10_m_above_ground",
                "surface",
            ],
            top_latitude=top_latitude,
            left_longitude=left_longitude,
            right_longitude=right_longitude,
            bottom_latitude=bottom_latitude,
        )

        output_directory_path = Path(
            output_directory
        )

        output_directory_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            output_directory_path
            / (
                f"gfs.{cycle.date}."
                f"{cycle.cycle_text}z."
                f"f{forecast_hour:03d}.grib2"
            )
        )

        result = await self.run_gfs_ingestion(
            url=url,
            output_path=str(output_path),
            latitude=latitude,
            longitude=longitude,
        )

        # Mark only after successful ingestion.
        self._last_gfs_cycles[location_key] = cycle_key

        await self._save_last_gfs_cycle(
            expected_persisted_cycle,
            latitude,
            longitude,
        )

        return result

    # ---------------------------------------------------------
    # ERA5
    # ---------------------------------------------------------

    async def run_era5_ingestion(
        self,
        latitude: float,
        longitude: float,
        date: str | None = None,
        output_directory: str = "data/era5",
    ):
        """
        Download, normalize and persist ERA5 data.

        ERA5IngestionService performs:
            CDS -> downloaded archive -> NetCDF -> normalization

        The scheduler then persists the normalized records
        through the existing WeatherRepository.
        """

        ingestion = ERA5IngestionService()

        target_date = (
            date
            or datetime.now(UTC).strftime("%Y-%m-%d")
        )

        output_directory_path = Path(
            output_directory
        )

        output_directory_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            output_directory_path
            / (
                f"era5_{latitude:.4f}_"
                f"{longitude:.4f}_"
                f"{target_date}.zip"
            )
        )

        try:
            records = await ingestion.ingest(
                latitude=latitude,
                longitude=longitude,
                date=target_date,
                output_path=output_path,
            )

            if records:
                await weather_repository.save_era5(
                    records
                )

            return records

        finally:
            await ingestion.client.close()

    # ---------------------------------------------------------
    # JOB REGISTRATION
    # ---------------------------------------------------------

    def add_current_weather_job(
        self,
        latitude: float,
        longitude: float,
        job_id: str | None = None,
    ) -> None:
        self.scheduler.add_job(
            self.run_current_ingestion,
            trigger="interval",
            minutes=self.interval_minutes,
            kwargs={
                "latitude": latitude,
                "longitude": longitude,
            },
            id=job_id or self.CURRENT_JOB_ID,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    def add_gfs_job(
        self,
        latitude: float,
        longitude: float,
        output_directory: str = "data/gfs",
        forecast_hour: int = 0,
        job_id: str | None = None,
    ) -> None:
        self.scheduler.add_job(
            self.run_automatic_gfs_ingestion,
            trigger="interval",
            minutes=self.interval_minutes,
            kwargs={
                "latitude": latitude,
                "longitude": longitude,
                "output_directory": output_directory,
                "forecast_hour": forecast_hour,
            },
            id=job_id or self.GFS_JOB_ID,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    def add_era5_job(
        self,
        latitude: float,
        longitude: float,
        output_directory: str = "data/era5",
        job_id: str | None = None,
    ) -> None:
        """
        Register periodic ERA5 ingestion.

        ERA5 is updated less frequently than real-time
        weather sources, so it runs every 6 hours.
        """

        self.scheduler.add_job(
            self.run_era5_ingestion,
            trigger="interval",
            hours=self.ERA5_INTERVAL_HOURS,
            kwargs={
                "latitude": latitude,
                "longitude": longitude,
                "output_directory": output_directory,
            },
            id=job_id or self.ERA5_JOB_ID,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # ---------------------------------------------------------
    # LIFECYCLE
    # ---------------------------------------------------------

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()

        if self.worker_pool is not None:
            asyncio.create_task(self.worker_pool.start())

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(
                wait=False
            )

    async def close(self) -> None:
        self.shutdown()

        await self.ingestion.close()
        await self.gfs_ingestion.close()

        if self.worker_pool is not None:
            await self.worker_pool.close()

        if self.redis_cache is not None:
            await self.redis_cache.close()