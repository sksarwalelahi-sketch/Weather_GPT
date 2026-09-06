from __future__ import annotations


class UnitConverter:
    """
    Convert common meteorological units into the canonical
    units used by the WeatherGPT data platform.

    Canonical units:
        temperature     -> °C
        pressure        -> hPa
        wind speed      -> km/h
        precipitation   -> mm
        humidity        -> %
        wind direction  -> degrees
    """

    @staticmethod
    def temperature_to_celsius(
        value: float,
        unit: str,
    ) -> float:
        normalized = unit.strip().lower()

        if normalized in {"c", "°c", "celsius"}:
            return float(value)

        if normalized in {
            "k",
            "kelvin",
        }:
            return float(value) - 273.15

        if normalized in {
            "f",
            "°f",
            "fahrenheit",
        }:
            return (float(value) - 32.0) * 5.0 / 9.0

        raise ValueError(
            f"Unsupported temperature unit: {unit}"
        )

    @staticmethod
    def pressure_to_hpa(
        value: float,
        unit: str,
    ) -> float:
        normalized = unit.strip().lower()

        if normalized in {
            "hpa",
            "mb",
            "millibar",
            "millibars",
        }:
            return float(value)

        if normalized in {
            "pa",
            "pascal",
            "pascals",
        }:
            return float(value) / 100.0

        if normalized in {
            "kpa",
        }:
            return float(value) * 10.0

        raise ValueError(
            f"Unsupported pressure unit: {unit}"
        )

    @staticmethod
    def wind_speed_to_kmh(
        value: float,
        unit: str,
    ) -> float:

        if value is None:
            raise ValueError("wind speed value cannot be None")

        if not unit:
            raise ValueError("wind-speed unit cannot be empty")

        normalized_unit = (
            unit.strip()
            .lower()
            .replace(" ", "")
            .replace("_", "")
        )

        # metres per second
        if normalized_unit in {
            "m/s",
            "mps",
            "ms-1",
            "ms^-1",
            "ms**-1",
        }:
            return float(value) * 3.6

        # kilometres per hour
        if normalized_unit in {
            "km/h",
            "kmh",
            "kph",
            "kmhr-1",
        }:
            return float(value)

        # miles per hour
        if normalized_unit in {
            "mph",
            "mi/h",
            "mihr-1",
        }:
            return float(value) * 1.609344

        raise ValueError(
            f"Unsupported wind-speed unit: {unit}"
        )
    @staticmethod
    def precipitation_to_mm(
        value: float,
        unit: str,
    ) -> float:
        normalized = unit.strip().lower()

        if normalized in {
            "mm",
            "millimeter",
            "millimeters",
        }:
            return float(value)

        if normalized in {
            "m",
            "meter",
            "meters",
        }:
            return float(value) * 1000.0

        if normalized in {
            "cm",
            "centimeter",
            "centimeters",
        }:
            return float(value) * 10.0

        raise ValueError(
            f"Unsupported precipitation unit: {unit}"
        )

    @staticmethod
    def humidity_to_percent(
        value: float,
        unit: str,
    ) -> float:
        normalized = unit.strip().lower()

        if normalized in {
            "%",
            "percent",
            "percentage",
        }:
            return float(value)

        if normalized in {
            "fraction",
            "ratio",
        }:
            return float(value) * 100.0

        raise ValueError(
            f"Unsupported humidity unit: {unit}"
        )

    @staticmethod
    def normalize_wind_direction(
        value: float,
    ) -> float:
        """
        Normalize a wind direction to [0, 360).
        """

        return float(value) % 360.0