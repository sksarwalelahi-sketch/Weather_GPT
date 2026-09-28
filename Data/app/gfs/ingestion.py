from __future__ import annotations

from pathlib import Path

from app.gfs.client import GFSClient, GFSData
from app.gfs.normalizer import GFSNormalizer, GFSPointWeather
from app.validation.weather_validator import (
    HumidityData,
    LocationData,
    PrecipitationData,
    PressureData,
    WindData,
)


class GFSIngestion:
    """
    GFS/NOMADS ingestion pipeline.

    Pipeline:

        NOAA NOMADS
             ↓
           GRIB2
             ↓
         GFSClient
             ↓
       GFSNormalizer
             ↓
          Validation
             ↓
         Repository
    """

    SOURCE = "noaa-gfs"

    def __init__(
        self,
        client: GFSClient | None = None,
        repository=None,
    ):
        self.client = client or GFSClient()
        self.repository = repository

    @staticmethod
    def validate_point(
        weather: GFSPointWeather,
    ) -> None:
        LocationData(
            latitude=weather.latitude,
            longitude=weather.longitude,
        )

        if weather.relative_humidity is not None:
            HumidityData(
                relative_humidity=weather.relative_humidity,
            )

        if weather.precipitation is not None:
            PrecipitationData(
                precipitation=weather.precipitation,
            )

        if weather.surface_pressure is not None:
            PressureData(
                surface_pressure=weather.surface_pressure,
            )

        if (
            weather.wind_speed is not None
            and weather.wind_direction is not None
        ):
            WindData(
                wind_speed=weather.wind_speed,
                wind_direction=weather.wind_direction,
            )

    def normalize_and_validate(
        self,
        dataset,
        latitude: float,
        longitude: float,
    ) -> GFSPointWeather:
        weather = GFSNormalizer.normalize_point(
            dataset=dataset,
            latitude=latitude,
            longitude=longitude,
        )

        self.validate_point(weather)

        return weather

    async def ingest_grib2(
        self,
        file_path: str | Path,
        latitude: float,
        longitude: float,
    ) -> GFSPointWeather:
        """
        Ingest an already-downloaded GRIB2 file.
        """

        gfs_data = self.client.parse_grib2(
            file_path,
        )

        weather = self.normalize_and_validate(
            dataset=gfs_data.dataset,
            latitude=latitude,
            longitude=longitude,
        )

        if self.repository is not None:
            save_method = getattr(
                self.repository,
                "save_gfs",
                None,
            )

            if save_method is not None:
                await save_method(weather)

        return weather

    async def ingest_data(
        self,
        data: GFSData,
        latitude: float,
        longitude: float,
    ) -> GFSPointWeather:
        """
        Ingest an already parsed GFS dataset.
        """

        weather = self.normalize_and_validate(
            dataset=data.dataset,
            latitude=latitude,
            longitude=longitude,
        )

        if self.repository is not None:
            save_method = getattr(
                self.repository,
                "save_gfs",
                None,
            )

            if save_method is not None:
                await save_method(weather)

        return weather

    async def ingest_remote(
        self,
        url: str,
        output_path: str | Path,
        latitude: float,
        longitude: float,
    ) -> GFSPointWeather:
        """
        Download a GRIB2 file from NOMADS and ingest it.
        """

        data = await self.client.get_grib2(
            url=url,
            output_path=output_path,
        )

        return await self.ingest_data(
            data=data,
            latitude=latitude,
            longitude=longitude,
        )

    async def close(self) -> None:
        await self.client.close()