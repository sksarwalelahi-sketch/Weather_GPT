from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.cache.redis_cache import RedisWeatherCache
from app.gfs.cycle import GFSCycleResolver
from app.gfs.ingestion import GFSIngestion
from app.ingestion.weather_ingestion import WeatherIngestion
from app.era5.ingestion import ERA5IngestionService
from app.core.dependencies import weather_repository


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

        self.interval_minutes = interval_minutes
        self.scheduler = AsyncIOScheduler()

        self._last_gfs_cycle = None

    # ---------------------------------------------------------
    # CURRENT WEATHER
    # ---------------------------------------------------------

    async def run_current_ingestion(
        self,
        latitude: float,
        longitude: float,
    ):
        return await self.ingestion.ingest_current(
            latitude=latitude,
            longitude=longitude,
        )

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
        return await self.gfs_ingestion.ingest_remote(
            url=url,
            output_path=output_path,
            latitude=latitude,
            longitude=longitude,
        )

    async def _get_last_gfs_cycle(self):
        if self.redis_cache is None:
            return None

        try:
            return await self.redis_cache.get(
                self.GFS_CYCLE_CACHE_KEY
            )
        except Exception:
            return None

    async def _save_last_gfs_cycle(
        self,
        cycle_key,
    ):
        if self.redis_cache is None:
            return

        try:
            await self.redis_cache.set(
                self.GFS_CYCLE_CACHE_KEY,
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
        cycle = GFSCycleResolver.resolve()

        cycle_key = (
            cycle.date,
            cycle.cycle,
            forecast_hour,
        )

        # In-memory protection.
        if cycle_key == self._last_gfs_cycle:
            return None

        # Persistent protection through Redis.
        persisted_cycle = (
            await self._get_last_gfs_cycle()
        )

        expected_persisted_cycle = {
            "date": cycle.date,
            "cycle": cycle.cycle,
            "forecast_hour": forecast_hour,
        }

        if persisted_cycle == expected_persisted_cycle:
            self._last_gfs_cycle = cycle_key
            return None

        url = GFSCycleResolver.build_url(
            forecast_hour=forecast_hour,
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
        self._last_gfs_cycle = cycle_key

        await self._save_last_gfs_cycle(
            expected_persisted_cycle
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
    ) -> None:
        self.scheduler.add_job(
            self.run_current_ingestion,
            trigger="interval",
            minutes=self.interval_minutes,
            kwargs={
                "latitude": latitude,
                "longitude": longitude,
            },
            id=self.CURRENT_JOB_ID,
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
            id=self.GFS_JOB_ID,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    def add_era5_job(
        self,
        latitude: float,
        longitude: float,
        output_directory: str = "data/era5",
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
            id=self.ERA5_JOB_ID,
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

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(
                wait=False
            )

    async def close(self) -> None:
        self.shutdown()

        await self.ingestion.close()
        await self.gfs_ingestion.close()

        if self.redis_cache is not None:
            await self.redis_cache.close()