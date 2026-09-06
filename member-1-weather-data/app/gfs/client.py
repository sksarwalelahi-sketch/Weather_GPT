from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cfgrib
import httpx
import xarray as xr


@dataclass(frozen=True)
class GFSData:
    dataset: xr.Dataset
    source: str = "noaa-gfs"


class GFSClient:
    BASE_URL = (
        "https://nomads.ncep.noaa.gov/cgi-bin/"
        "filter_gfs_0p25.pl"
    )

    def __init__(self, timeout: float = 30.0):
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")

        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    # ------------------------------------------------------------------
    # URL BUILDING
    # ------------------------------------------------------------------

    @staticmethod
    def build_url(
        date: str,
        cycle: int,
        forecast_hour: int,
        file_name: str = "gfs.t00z.pgrb2.0p25.f000",
        variables: list[str] | None = None,
        levels: list[str] | None = None,
        top_latitude: float | None = None,
        left_longitude: float | None = None,
        right_longitude: float | None = None,
        bottom_latitude: float | None = None,
    ) -> str:

        if len(date) != 8 or not date.isdigit():
            raise ValueError("date must be in YYYYMMDD format")

        if cycle not in {0, 6, 12, 18}:
            raise ValueError("cycle must be one of 0, 6, 12, 18")

        if not 0 <= forecast_hour <= 384:
            raise ValueError("forecast_hour must be between 0 and 384")

        cycle_text = f"{cycle:02d}"
        cycle_with_z = f"{cycle_text}z"

        if file_name == "gfs.t00z.pgrb2.0p25.f000":
            file_name = (
                f"gfs.t{cycle_with_z}.pgrb2.0p25."
                f"f{forecast_hour:03d}"
            )

        url = (
            f"{GFSClient.BASE_URL}"
            f"?dir=%2Fgfs.{date}%2F{cycle_text}%2Fatmos"
            f"&file={file_name}"
        )

        if variables:
            for variable in variables:
                url += f"&var_{variable}=on"

        if levels:
            for level in levels:
                url += f"&lev_{level}=on"

        bounds = [
            top_latitude,
            left_longitude,
            right_longitude,
            bottom_latitude,
        ]

        if any(value is not None for value in bounds):
            if not all(value is not None for value in bounds):
                raise ValueError(
                    "all four geographic bounds must be supplied together"
                )

            url += (
                f"&subregion="
                f"&toplat={top_latitude}"
                f"&leftlon={left_longitude}"
                f"&rightlon={right_longitude}"
                f"&bottomlat={bottom_latitude}"
            )

        return url


        

    # ------------------------------------------------------------------
    # DOWNLOAD
    # ------------------------------------------------------------------

    async def download_grib2(
        self,
        url: str,
        output_path: str | Path,
    ) -> Path:

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = path.with_suffix(path.suffix + ".part")

        try:
            async with self.client.stream("GET", url) as response:
                response.raise_for_status()

                with temporary_path.open("wb") as file:
                    async for chunk in response.aiter_bytes(
                        chunk_size=1024 * 1024
                    ):
                        file.write(chunk)

            if not temporary_path.exists():
                raise RuntimeError(
                    "GFS download did not create an output file"
                )

            if temporary_path.stat().st_size == 0:
                raise ValueError(
                    "Downloaded GFS GRIB2 file is empty"
                )

            temporary_path.replace(path)

            return path

        except Exception:
            if temporary_path.exists():
                temporary_path.unlink()

            raise

    # ------------------------------------------------------------------
    # BASIC GRIB OPEN
    # ------------------------------------------------------------------

    @staticmethod
    def open_grib2(file_path: str | Path) -> xr.Dataset:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"GFS GRIB2 file not found: {path}"
            )

        if path.stat().st_size == 0:
            raise ValueError(
                f"GFS GRIB2 file is empty: {path}"
            )

        return xr.open_dataset(
            path,
            engine="cfgrib",
        )

    # ------------------------------------------------------------------
    # MULTI-DATASET GRIB DISCOVERY
    # ------------------------------------------------------------------

    @staticmethod
    def open_grib2_datasets(
        file_path: str | Path,
    ) -> list[xr.Dataset]:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"GFS GRIB2 file not found: {path}"
            )

        if path.stat().st_size == 0:
            raise ValueError(
                f"GFS GRIB2 file is empty: {path}"
            )

        datasets = cfgrib.open_datasets(
            str(path),
            backend_kwargs={
                "indexpath": "",
            },
        )

        return list(datasets)

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    @staticmethod
    def _find_dataset(
        datasets: list[xr.Dataset],
        required_variables: set[str],
    ) -> xr.Dataset | None:

        for dataset in datasets:
            available = set(dataset.data_vars)

            if required_variables.issubset(available):
                return dataset

        return None

    @staticmethod
    def _find_variable_dataset(
        datasets: list[xr.Dataset],
        variable: str,
    ) -> xr.Dataset | None:

        for dataset in datasets:
            if variable in dataset.data_vars:
                return dataset

        return None

    @staticmethod
    def _clean_data_array(
        data_array: xr.DataArray,
    ) -> xr.DataArray:

        # Keep only dimension coordinates.
        # This removes GRIB-specific scalar coordinates such as:
        # heightAboveGround, isobaricInhPa, etc.
        coords = {}

        for dimension in data_array.dims:
            if dimension in data_array.coords:
                coords[dimension] = data_array.coords[dimension].values

        return xr.DataArray(
            data_array.values,
            dims=data_array.dims,
            coords=coords,
            attrs=dict(data_array.attrs),
            name=data_array.name,
        )

    # ------------------------------------------------------------------
    # WEATHER DATASET EXTRACTION
    # ------------------------------------------------------------------

    @classmethod
    def open_weather_dataset(
        cls,
        file_path: str | Path,
    ) -> xr.Dataset:

        datasets = cls.open_grib2_datasets(file_path)

        if not datasets:
            raise ValueError(
                "No logical datasets were found in the GFS GRIB2 file"
            )

        try:
            # ----------------------------------------------------------
            # 1. Temperature + Relative Humidity
            #
            # Real GFS file:
            # dataset 7 -> t2m + r2
            # ----------------------------------------------------------

            temperature_humidity = cls._find_dataset(
                datasets,
                {"t2m", "r2"},
            )

            if temperature_humidity is None:
                temperature_humidity = cls._find_variable_dataset(
                    datasets,
                    "t2m",
                )

            if temperature_humidity is None:
                raise ValueError(
                    "GFS GRIB2 file does not contain 2 m temperature (t2m)"
                )

            # ----------------------------------------------------------
            # 2. 10 m Wind
            #
            # Real GFS file:
            # dataset 6 -> u10 + v10
            # ----------------------------------------------------------

            wind = cls._find_dataset(
                datasets,
                {"u10", "v10"},
            )

            # ----------------------------------------------------------
            # 3. Surface Pressure
            #
            # Real GFS file:
            # dataset 25 -> t + sp
            # ----------------------------------------------------------

            pressure = cls._find_variable_dataset(
                datasets,
                "sp",
            )

            # ----------------------------------------------------------
            # Build clean canonical dataset
            # ----------------------------------------------------------

            data_vars: dict[str, xr.DataArray] = {}

            data_vars["t2m"] = cls._clean_data_array(
                temperature_humidity["t2m"]
            )

            if "r2" in temperature_humidity:
                data_vars["r2"] = cls._clean_data_array(
                    temperature_humidity["r2"]
                )

            if wind is not None:
                data_vars["u10"] = cls._clean_data_array(
                    wind["u10"]
                )

                data_vars["v10"] = cls._clean_data_array(
                    wind["v10"]
                )

            if pressure is not None:
                data_vars["sp"] = cls._clean_data_array(
                    pressure["sp"]
                )

            weather_dataset = xr.Dataset(data_vars)

            # ----------------------------------------------------------
            # Carry common temporal/geographical coordinates from the
            # temperature dataset.
            # ----------------------------------------------------------

            for coordinate in (
                "latitude",
                "longitude",
                "time",
                "step",
                "valid_time",
            ):
                if coordinate in temperature_humidity.coords:
                    weather_dataset = weather_dataset.assign_coords(
                        {
                            coordinate: temperature_humidity[
                                coordinate
                            ].values
                        }
                    )

            weather_dataset.attrs["source"] = "noaa-gfs"

            return weather_dataset

        finally:
            # The selected variables were copied into memory by
            # _clean_data_array(), so the cfgrib-backed datasets can
            # safely be closed here.
            for dataset in datasets:
                try:
                    dataset.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # PARSING
    # ------------------------------------------------------------------

    @classmethod
    def parse_grib2(
        cls,
        file_path: str | Path,
    ) -> GFSData:

        dataset = cls.open_weather_dataset(file_path)

        return GFSData(
            dataset=dataset,
            source="noaa-gfs",
        )

    # ------------------------------------------------------------------
    # REMOTE DOWNLOAD + PARSE
    # ------------------------------------------------------------------

    async def get_grib2(
        self,
        url: str,
        output_path: str | Path,
    ) -> GFSData:

        path = await self.download_grib2(
            url=url,
            output_path=output_path,
        )

        return self.parse_grib2(path)

    # ------------------------------------------------------------------
    # CLOSE HTTP CLIENT
    # ------------------------------------------------------------------

    async def close(self) -> None:
        await self.client.aclose()