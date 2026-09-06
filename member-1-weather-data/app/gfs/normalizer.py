from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import xarray as xr
from pydantic import BaseModel

from app.normalization.unit_converter import UnitConverter


class GFSPointWeather(BaseModel):
    """
    Canonical weather representation for a single GFS grid point.
    """

    latitude: float
    longitude: float

    valid_at: datetime

    temperature: float
    relative_humidity: float | None = None
    surface_pressure: float | None = None

    wind_speed: float | None = None
    wind_direction: float | None = None

    precipitation: float | None = None

    source: str = "noaa-gfs"


class GFSNormalizer:
    """
    Converts an xarray GFS dataset into a point-based weather model.

    GFS variable names vary between GRIB products, so variable
    resolution is handled explicitly rather than assuming every
    dataset contains every weather field.

    When GRIB/xarray unit metadata is available, values are converted
    into the canonical WeatherGPT units:

        temperature     -> °C
        pressure        -> hPa
        wind speed      -> km/h
        precipitation   -> mm
        humidity        -> %
        wind direction  -> degrees

    If unit metadata is unavailable, the existing raw value is retained
    for backwards compatibility with datasets that do not expose units.
    """

    SOURCE = "noaa-gfs"

    TEMPERATURE_VARIABLES = (
        "t2m",
        "2t",
        "temperature",
    )

    PRESSURE_VARIABLES = (
        "sp",
        "mslet",
        "prmsl",
        "surface_pressure",
    )

    HUMIDITY_VARIABLES = (
        "r2",
        "2r",
        "relative_humidity",
    )

    U_WIND_VARIABLES = (
        "u10",
        "10u",
        "u",
    )

    V_WIND_VARIABLES = (
        "v10",
        "10v",
        "v",
    )

    PRECIPITATION_VARIABLES = (
        "tp",
        "prate",
        "precipitation",
    )

    @classmethod
    def _find_variable(
        cls,
        dataset: xr.Dataset,
        candidates: tuple[str, ...],
    ) -> str | None:
        for name in candidates:
            if name in dataset.data_vars:
                return name

        return None

    @staticmethod
    def _scalar(
        value,
    ) -> float:
        array = np.asarray(value)

        if array.size != 1:
            raise ValueError(
                "Expected a single scalar grid-point value"
            )

        result = float(array.reshape(-1)[0])

        if not np.isfinite(result):
            raise ValueError(
                "GFS value is not finite"
            )

        return result

    @staticmethod
    def _find_coordinate(
        dataset: xr.Dataset,
        candidates: tuple[str, ...],
    ) -> str | None:
        for name in candidates:
            if name in dataset.coords:
                return name

        return None

    @staticmethod
    def _get_units(
        dataset: xr.Dataset,
        variable: str,
    ) -> str | None:
        units = dataset[variable].attrs.get("units")

        if units is None:
            return None

        units = str(units).strip()

        return units or None

    @classmethod
    def _convert_temperature(
        cls,
        dataset: xr.Dataset,
        variable: str,
        value: float,
    ) -> float:
        units = cls._get_units(
            dataset,
            variable,
        )

        if units is None:
            return value

        return UnitConverter.temperature_to_celsius(
            value,
            units,
        )

    @classmethod
    def _convert_pressure(
        cls,
        dataset: xr.Dataset,
        variable: str,
        value: float,
    ) -> float:
        units = cls._get_units(
            dataset,
            variable,
        )

        if units is None:
            return value

        return UnitConverter.pressure_to_hpa(
            value,
            units,
        )

    @classmethod
    def _convert_humidity(
        cls,
        dataset: xr.Dataset,
        variable: str,
        value: float,
    ) -> float:
        units = cls._get_units(
            dataset,
            variable,
        )

        if units is None:
            return value

        return UnitConverter.humidity_to_percent(
            value,
            units,
        )

    @classmethod
    def _convert_precipitation(
        cls,
        dataset: xr.Dataset,
        variable: str,
        value: float,
    ) -> float:
        units = cls._get_units(
            dataset,
            variable,
        )

        if units is None:
            return value

        return UnitConverter.precipitation_to_mm(
            value,
            units,
        )

    @classmethod
    def _convert_wind_speed(
        cls,
        dataset: xr.Dataset,
        variable: str,
        value: float,
    ) -> float:
        units = cls._get_units(
            dataset,
            variable,
        )

        if units is None:
            return value

        return UnitConverter.wind_speed_to_kmh(
            value,
            units,
        )

    @classmethod
    def normalize_point(
        cls,
        dataset: xr.Dataset,
        latitude: float,
        longitude: float,
    ) -> GFSPointWeather:
        """
        Extract the nearest GFS grid point to a requested location.
        """

        latitude_coord = cls._find_coordinate(
            dataset,
            ("latitude", "lat"),
        )

        longitude_coord = cls._find_coordinate(
            dataset,
            ("longitude", "lon"),
        )

        if latitude_coord is None:
            raise ValueError(
                "GFS dataset does not contain latitude coordinates"
            )

        if longitude_coord is None:
            raise ValueError(
                "GFS dataset does not contain longitude coordinates"
            )

        point = dataset.sel(
            {
                latitude_coord: latitude,
                longitude_coord: longitude,
            },
            method="nearest",
        )

        temperature_variable = cls._find_variable(
            dataset,
            cls.TEMPERATURE_VARIABLES,
        )

        if temperature_variable is None:
            raise ValueError(
                "GFS dataset does not contain a temperature variable"
            )

        temperature = cls._scalar(
            point[temperature_variable].values
        )

        temperature = cls._convert_temperature(
            dataset,
            temperature_variable,
            temperature,
        )

        humidity_variable = cls._find_variable(
            dataset,
            cls.HUMIDITY_VARIABLES,
        )

        pressure_variable = cls._find_variable(
            dataset,
            cls.PRESSURE_VARIABLES,
        )

        u_variable = cls._find_variable(
            dataset,
            cls.U_WIND_VARIABLES,
        )

        v_variable = cls._find_variable(
            dataset,
            cls.V_WIND_VARIABLES,
        )

        precipitation_variable = cls._find_variable(
            dataset,
            cls.PRECIPITATION_VARIABLES,
        )

        relative_humidity = None

        if humidity_variable is not None:
            relative_humidity = cls._scalar(
                point[humidity_variable].values
            )

            relative_humidity = cls._convert_humidity(
                dataset,
                humidity_variable,
                relative_humidity,
            )

        surface_pressure = None

        if pressure_variable is not None:
            surface_pressure = cls._scalar(
                point[pressure_variable].values
            )

            surface_pressure = cls._convert_pressure(
                dataset,
                pressure_variable,
                surface_pressure,
            )

        wind_speed = None
        wind_direction = None

        if (
            u_variable is not None
            and v_variable is not None
        ):
            u_wind = cls._scalar(
                point[u_variable].values
            )

            v_wind = cls._scalar(
                point[v_variable].values
            )

            wind_speed = float(
                np.sqrt(
                    u_wind**2
                    + v_wind**2
                )
            )

            wind_units = cls._get_units(
                dataset,
                u_variable,
            )

            if wind_units is not None:
                wind_speed = UnitConverter.wind_speed_to_kmh(
                    wind_speed,
                    wind_units,
                )

            wind_direction = float(
                (
                    np.degrees(
                        np.arctan2(
                            -u_wind,
                            -v_wind,
                        )
                    )
                    + 360
                )
                % 360
            )

            wind_direction = UnitConverter.normalize_wind_direction(
                wind_direction
            )

        precipitation = None

        if precipitation_variable is not None:
            precipitation = cls._scalar(
                point[precipitation_variable].values
            )

            precipitation = cls._convert_precipitation(
                dataset,
                precipitation_variable,
                precipitation,
            )

        valid_at = cls._extract_valid_time(
            point
        )

        return GFSPointWeather(
            latitude=latitude,
            longitude=longitude,
            valid_at=valid_at,
            temperature=temperature,
            relative_humidity=relative_humidity,
            surface_pressure=surface_pressure,
            wind_speed=wind_speed,
            wind_direction=wind_direction,
            precipitation=precipitation,
            source=cls.SOURCE,
        )

    @staticmethod
    def _extract_valid_time(
        dataset: xr.Dataset,
    ) -> datetime:
        for name in (
            "valid_time",
            "time",
        ):
            if name in dataset.coords:
                value = dataset[name].values

                array = np.asarray(value)

                if array.size == 0:
                    continue

                timestamp = array.reshape(-1)[0]

                if isinstance(
                    timestamp,
                    np.datetime64,
                ):
                    seconds = (
                        timestamp.astype(
                            "datetime64[s]"
                        ).astype(int)
                    )

                    return datetime.fromtimestamp(
                        seconds,
                        tz=timezone.utc,
                    )

                if isinstance(
                    timestamp,
                    datetime,
                ):
                    if timestamp.tzinfo is None:
                        return timestamp.replace(
                            tzinfo=timezone.utc
                        )

                    return timestamp

        return datetime.now(timezone.utc)