from __future__ import annotations

from datetime import datetime, timezone
from math import atan2, degrees, sqrt

import numpy as np
import xarray as xr


class ERA5Normalizer:
    SOURCE = "era5"

    @staticmethod
    def _to_celsius(value: float) -> float:
        return float(value) - 273.15

    @staticmethod
    def _to_hpa(value: float) -> float:
        return float(value) / 100.0

    @staticmethod
    def _wind_speed_kmh(u: float, v: float) -> float:
        return sqrt(float(u) ** 2 + float(v) ** 2) * 3.6

    @staticmethod
    def _wind_direction(u: float, v: float) -> float:
        direction = (degrees(atan2(-float(u), -float(v))) + 360.0) % 360.0
        return direction

    @staticmethod
    def _precipitation_mm(value_m: float) -> float:
        return float(value_m) * 1000.0

    @staticmethod
    def _find_variable(
        dataset: xr.Dataset,
        candidates: list[str],
    ) -> str:
        for name in candidates:
            if name in dataset.data_vars:
                return name

        raise KeyError(
            f"ERA5 dataset is missing required variable. "
            f"Tried: {candidates}"
        )

    @staticmethod
    def _scalar_value(data_array: xr.DataArray) -> float:
        """
        Convert a selected ERA5 DataArray into one scalar value.

        ERA5 files normally contain a time dimension. After selecting
        latitude/longitude, the DataArray may still contain one time value.
        """
        values = np.asarray(data_array.values)

        if values.size == 0:
            raise ValueError("ERA5 variable contains no data")

        return float(values.reshape(-1)[0])

    @staticmethod
    def _extract_time(dataset: xr.Dataset) -> datetime:
        for name in ("valid_time", "time"):

            if name not in dataset.coords:
                continue

            values = np.asarray(dataset[name].values)

            if values.size == 0:
                continue

            value = values.reshape(-1)[0]

            # NumPy datetime64 → Python datetime
            if isinstance(value, np.datetime64):
                if np.isnat(value):
                    continue

                value = value.astype("datetime64[us]").tolist()

            # xarray/pandas-like datetime objects
            elif hasattr(value, "to_pydatetime"):
                value = value.to_pydatetime()

            if isinstance(value, datetime):

                if value.tzinfo is None:
                    return value.replace(tzinfo=timezone.utc)

                return value.astimezone(timezone.utc)

        raise ValueError(
            "ERA5 dataset does not contain a usable time coordinate"
        )

    @classmethod
    def normalize_point(
        cls,
        dataset: xr.Dataset,
        latitude: float,
        longitude: float,
    ) -> dict:

        if not isinstance(dataset, xr.Dataset):
            raise TypeError("dataset must be an xarray.Dataset")

        if not -90.0 <= latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")

        if not -180.0 <= longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180")

        # Select the nearest ERA5 grid point.
        selected = dataset.sel(
            latitude=latitude,
            longitude=longitude,
            method="nearest",
        )

        temperature_variable = cls._find_variable(
            selected,
            ["t2m", "2m_temperature"],
        )

        dewpoint_variable = cls._find_variable(
            selected,
            ["d2m", "2m_dewpoint_temperature"],
        )

        u_variable = cls._find_variable(
            selected,
            ["u10", "10m_u_component_of_wind"],
        )

        v_variable = cls._find_variable(
            selected,
            ["v10", "10m_v_component_of_wind"],
        )

        pressure_variable = cls._find_variable(
            selected,
            ["sp", "surface_pressure"],
        )

        precipitation_variable = cls._find_variable(
            selected,
            ["tp", "total_precipitation"],
        )

        temperature = cls._to_celsius(
            cls._scalar_value(selected[temperature_variable])
        )

        dewpoint = cls._to_celsius(
            cls._scalar_value(selected[dewpoint_variable])
        )

        u10 = cls._scalar_value(selected[u_variable])
        v10 = cls._scalar_value(selected[v_variable])

        surface_pressure = cls._to_hpa(
            cls._scalar_value(selected[pressure_variable])
        )

        precipitation = cls._precipitation_mm(
            cls._scalar_value(selected[precipitation_variable])
        )

        wind_speed = cls._wind_speed_kmh(u10, v10)

        wind_direction = cls._wind_direction(u10, v10)

        observed_at = cls._extract_time(selected)

        return {
            "latitude": float(latitude),
            "longitude": float(longitude),
            "observed_at": observed_at,
            "temperature": temperature,
            "dewpoint": dewpoint,
            "surface_pressure": surface_pressure,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "precipitation": precipitation,
            "source": cls.SOURCE,
        }