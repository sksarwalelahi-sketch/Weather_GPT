import numpy as np
import pytest
import xarray as xr

from app.gfs.normalizer import (
    GFSNormalizer,
)


def make_gfs_dataset():
    return xr.Dataset(
        data_vars={
            "t2m": (
                ("latitude", "longitude"),
                np.array([[300.15]]),
            ),
            "r2": (
                ("latitude", "longitude"),
                np.array([[75.0]]),
            ),
            "sp": (
                ("latitude", "longitude"),
                np.array([[100500.0]]),
            ),
            "u10": (
                ("latitude", "longitude"),
                np.array([[3.0]]),
            ),
            "v10": (
                ("latitude", "longitude"),
                np.array([[4.0]]),
            ),
            "tp": (
                ("latitude", "longitude"),
                np.array([[2.5]]),
            ),
        },
        coords={
            "latitude": [20.2961],
            "longitude": [85.8245],
            "time": np.array(
                ["2026-08-30T12:00:00"],
                dtype="datetime64[ns]",
            ),
        },
    )


def test_gfs_normalizer_source():
    assert GFSNormalizer.SOURCE == "noaa-gfs"


def test_find_temperature_variable():
    dataset = make_gfs_dataset()

    variable = GFSNormalizer._find_variable(
        dataset,
        GFSNormalizer.TEMPERATURE_VARIABLES,
    )

    assert variable == "t2m"


def test_find_pressure_variable():
    dataset = make_gfs_dataset()

    variable = GFSNormalizer._find_variable(
        dataset,
        GFSNormalizer.PRESSURE_VARIABLES,
    )

    assert variable == "sp"


def test_missing_temperature_is_rejected():
    dataset = make_gfs_dataset().drop_vars("t2m")

    with pytest.raises(ValueError):
        GFSNormalizer.normalize_point(
            dataset,
            latitude=20.2961,
            longitude=85.8245,
        )


def test_missing_latitude_is_rejected():
    dataset = make_gfs_dataset().drop_indexes(
        "latitude"
    ).drop_vars(
        "latitude"
    )

    with pytest.raises(ValueError):
        GFSNormalizer.normalize_point(
            dataset,
            latitude=20.2961,
            longitude=85.8245,
        )


def test_normalize_gfs_point():
    dataset = make_gfs_dataset()

    result = GFSNormalizer.normalize_point(
        dataset,
        latitude=20.2961,
        longitude=85.8245,
    )

    assert result.latitude == 20.2961
    assert result.longitude == 85.8245

    assert result.temperature == pytest.approx(
        300.15
    )

    assert result.relative_humidity == pytest.approx(
        75.0
    )

    assert result.surface_pressure == pytest.approx(
        100500.0
    )

    assert result.wind_speed == pytest.approx(
        5.0
    )

    assert result.precipitation == pytest.approx(
        2.5
    )

    assert result.source == "noaa-gfs"


def test_wind_direction_from_u_v():
    dataset = make_gfs_dataset()

    result = GFSNormalizer.normalize_point(
        dataset,
        latitude=20.2961,
        longitude=85.8245,
    )

    assert result.wind_direction == pytest.approx(
        216.8699,
        abs=0.01,
    )


def test_optional_variables_can_be_missing():
    dataset = make_gfs_dataset().drop_vars(
        [
            "r2",
            "sp",
            "tp",
        ]
    )

    result = GFSNormalizer.normalize_point(
        dataset,
        latitude=20.2961,
        longitude=85.8245,
    )

    assert result.temperature == pytest.approx(
        300.15
    )

    assert result.relative_humidity is None
    assert result.surface_pressure is None
    assert result.precipitation is None

    assert result.wind_speed == pytest.approx(
        5.0
    )
    
def test_gfs_temperature_units_are_converted():
    dataset = make_gfs_dataset()

    dataset["t2m"].attrs["units"] = "K"

    result = GFSNormalizer.normalize_point(
        dataset,
        latitude=20.2961,
        longitude=85.8245,
    )

    assert result.temperature == pytest.approx(
        27.0
    )


def test_gfs_pressure_units_are_converted():
    dataset = make_gfs_dataset()

    dataset["sp"].attrs["units"] = "Pa"

    result = GFSNormalizer.normalize_point(
        dataset,
        latitude=20.2961,
        longitude=85.8245,
    )

    assert result.surface_pressure == pytest.approx(
        1005.0
    )


def test_gfs_wind_units_are_converted():
    dataset = make_gfs_dataset()

    dataset["u10"].attrs["units"] = "m/s"
    dataset["v10"].attrs["units"] = "m/s"

    result = GFSNormalizer.normalize_point(
        dataset,
        latitude=20.2961,
        longitude=85.8245,
    )

    assert result.wind_speed == pytest.approx(
        18.0
    )


def test_gfs_precipitation_units_are_converted():
    dataset = make_gfs_dataset()

    dataset["tp"].attrs["units"] = "m"

    result = GFSNormalizer.normalize_point(
        dataset,
        latitude=20.2961,
        longitude=85.8245,
    )

    assert result.precipitation == pytest.approx(
        2500.0
    )


def test_gfs_missing_units_preserve_existing_behavior():
    dataset = make_gfs_dataset()

    result = GFSNormalizer.normalize_point(
        dataset,
        latitude=20.2961,
        longitude=85.8245,
    )

    assert result.temperature == pytest.approx(
        300.15
    )

    assert result.surface_pressure == pytest.approx(
        100500.0
    )

    assert result.wind_speed == pytest.approx(
        5.0
    )

    assert result.precipitation == pytest.approx(
        2.5
    )