from __future__ import annotations

import asyncio
import zipfile
from datetime import date as date_type
from pathlib import Path

import cdsapi


class ERA5Client:
    DATASET = "reanalysis-era5-single-levels"

    VARIABLES = [
        "2m_temperature",
        "2m_dewpoint_temperature",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "surface_pressure",
        "total_precipitation",
    ]

    def __init__(self, client=None):
        self.client = client or cdsapi.Client()

    @staticmethod
    def _validate_coordinates(latitude: float, longitude: float) -> None:
        if not -90.0 <= latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")

        if not -180.0 <= longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180")

    @staticmethod
    def _validate_date(value: str) -> None:
        if len(value) != 10:
            raise ValueError("date must use YYYY-MM-DD format")

        try:
            date_type.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("date must use YYYY-MM-DD format") from exc

    @staticmethod
    def _build_area(latitude: float, longitude: float) -> list[float]:
        delta = 0.25

        north = min(90.0, latitude + delta)
        west = max(-180.0, longitude - delta)
        south = max(-90.0, latitude - delta)
        east = min(180.0, longitude + delta)

        return [north, west, south, east]

    @staticmethod
    def _extract_zip(zip_path: Path, output_dir: Path) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(output_dir)

            files = [
                output_dir / name
                for name in archive.namelist()
                if name.endswith(".nc")
            ]

        if not files:
            raise RuntimeError(
                "ERA5 CDS response did not contain any NetCDF files"
            )

        return files

    async def download(
        self,
        latitude: float,
        longitude: float,
        date: str,
        output_path: str | Path,
        hours: list[str] | None = None,
    ) -> Path:

        self._validate_coordinates(latitude, longitude)
        self._validate_date(date)

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        request_hours = hours or [
            "00:00",
            "06:00",
            "12:00",
            "18:00",
        ]

        request = {
            "product_type": "reanalysis",
            "variable": self.VARIABLES,
            "year": date[0:4],
            "month": date[5:7],
            "day": date[8:10],
            "time": request_hours,
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": self._build_area(latitude, longitude),
        }

        await asyncio.to_thread(
            self.client.retrieve,
            self.DATASET,
            request,
            str(output),
        )

        if not output.exists():
            raise RuntimeError(
                f"ERA5 download did not create expected file: {output}"
            )

        # CDS currently returns a ZIP container even when the requested
        # data format is NetCDF. Extract the contained NetCDF files.
        if zipfile.is_zipfile(output):
            extraction_dir = output.parent / f"{output.stem}_extracted"

            self._extract_zip(
                zip_path=output,
                output_dir=extraction_dir,
            )

        return output

    async def close(self) -> None:
        return None