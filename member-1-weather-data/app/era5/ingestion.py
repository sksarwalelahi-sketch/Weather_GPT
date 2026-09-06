from __future__ import annotations

import zipfile
from pathlib import Path

import xarray as xr

from app.era5.client import ERA5Client
from app.era5.normalizer import ERA5Normalizer


class ERA5IngestionService:
    def __init__(
        self,
        client: ERA5Client | None = None,
    ):
        self.client = client or ERA5Client()

    @staticmethod
    def _find_files(extracted_dir: Path) -> tuple[Path, Path]:
        instant_files = list(
            extracted_dir.glob("*stepType-instant.nc")
        )

        accum_files = list(
            extracted_dir.glob("*stepType-accum.nc")
        )

        if not instant_files:
            raise FileNotFoundError(
                "ERA5 instant NetCDF file was not found"
            )

        if not accum_files:
            raise FileNotFoundError(
                "ERA5 accumulated NetCDF file was not found"
            )

        return instant_files[0], accum_files[0]

    @staticmethod
    def _extract_download(
        archive_path: Path,
    ) -> Path:

        extracted_dir = (
            archive_path.parent
            / f"{archive_path.stem}_ingested"
        )

        extracted_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        with zipfile.ZipFile(archive_path, "r") as archive:
            archive.extractall(extracted_dir)

        return extracted_dir

    async def ingest(
        self,
        latitude: float,
        longitude: float,
        date: str,
        output_path: str | Path,
    ) -> list[dict]:

        archive_path = await self.client.download(
            latitude=latitude,
            longitude=longitude,
            date=date,
            output_path=output_path,
        )

        # The client already extracts the CDS ZIP into
        # <stem>_extracted. Reuse that directory.
        extracted_dir = (
            archive_path.parent
            / f"{archive_path.stem}_extracted"
        )

        if not extracted_dir.exists():
            if not zipfile.is_zipfile(archive_path):
                raise RuntimeError(
                    "ERA5 download is not a ZIP archive and "
                    "no extracted directory was found"
                )

            extracted_dir = self._extract_download(
                archive_path
            )

        instant_path, accum_path = self._find_files(
            extracted_dir
        )

        instant = xr.open_dataset(
            instant_path,
            engine="netcdf4",
        )

        accum = xr.open_dataset(
            accum_path,
            engine="netcdf4",
        )

        try:
            dataset = xr.merge(
                [instant, accum],
                compat="override",
            )

            results = []

            times = dataset["valid_time"].values

            for index in range(len(times)):
                point_dataset = dataset.isel(
                    valid_time=index
                )

                normalized = (
                    ERA5Normalizer.normalize_point(
                        point_dataset,
                        latitude=latitude,
                        longitude=longitude,
                    )
                )

                results.append(normalized)

            return results

        finally:
            instant.close()
            accum.close()