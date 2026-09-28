import numpy as np
import pytest
import xarray as xr

import app.gfs.client as gfs_client_module
from app.gfs.client import GFSClient


def make_dataset(
    variables: dict[str, float],
    units: dict[str, str],
    height: float | None = None,
) -> xr.Dataset:

    data_vars = {}

    for name, value in variables.items():
        data_vars[name] = (
            ("latitude", "longitude"),
            np.array([[value]], dtype=float),
        )

    coords = {
        "latitude": [20.25],
        "longitude": [85.75],
        "time": np.datetime64("2026-08-30T06:00:00"),
        "valid_time": np.datetime64("2026-08-30T09:00:00"),
    }

    if height is not None:
        coords["heightAboveGround"] = height

    dataset = xr.Dataset(
        data_vars,
        coords=coords,
    )

    for name, unit in units.items():
        dataset[name].attrs["units"] = unit

    return dataset


def test_open_weather_dataset_selects_required_gfs_groups(
    tmp_path,
    monkeypatch,
):

    grib_file = tmp_path / "weather.grib2"
    grib_file.write_bytes(b"fake-grib")

    irrelevant = make_dataset(
        {"t": 290.0},
        {"t": "K"},
    )

    temperature_humidity = make_dataset(
        {
            "t2m": 300.0,
            "r2": 88.0,
        },
        {
            "t2m": "K",
            "r2": "%",
        },
        height=2,
    )

    wind = make_dataset(
        {
            "u10": 4.0,
            "v10": -1.0,
        },
        {
            "u10": "m s-1",
            "v10": "m s-1",
        },
        height=10,
    )

    pressure = make_dataset(
        {
            "t": 300.0,
            "sp": 100000.0,
        },
        {
            "t": "K",
            "sp": "Pa",
        },
    )

    monkeypatch.setattr(
        gfs_client_module.cfgrib,
        "open_datasets",
        lambda *args, **kwargs: [
            irrelevant,
            temperature_humidity,
            wind,
            pressure,
        ],
    )

    dataset = GFSClient.open_weather_dataset(grib_file)

    assert set(dataset.data_vars) == {
        "t2m",
        "r2",
        "u10",
        "v10",
        "sp",
    }

    assert dataset["t2m"].attrs["units"] == "K"
    assert dataset["r2"].attrs["units"] == "%"

    assert float(dataset["t2m"].values[0][0]) == 300.0
    assert float(dataset["r2"].values[0][0]) == 88.0
    assert float(dataset["u10"].values[0][0]) == 4.0
    assert float(dataset["v10"].values[0][0]) == -1.0
    assert float(dataset["sp"].values[0][0]) == 100000.0


def test_open_weather_dataset_requires_temperature(
    tmp_path,
    monkeypatch,
):

    grib_file = tmp_path / "weather.grib2"
    grib_file.write_bytes(b"fake-grib")

    wind = make_dataset(
        {
            "u10": 4.0,
            "v10": -1.0,
        },
        {
            "u10": "m s-1",
            "v10": "m s-1",
        },
        height=10,
    )

    monkeypatch.setattr(
        gfs_client_module.cfgrib,
        "open_datasets",
        lambda *args, **kwargs: [wind],
    )

    with pytest.raises(
        ValueError,
        match="2 m temperature",
    ):
        GFSClient.open_weather_dataset(grib_file)


def test_parse_grib2_returns_gfs_data(
    tmp_path,
    monkeypatch,
):

    grib_file = tmp_path / "weather.grib2"
    grib_file.write_bytes(b"fake-grib")

    temperature_humidity = make_dataset(
        {
            "t2m": 300.0,
            "r2": 88.0,
        },
        {
            "t2m": "K",
            "r2": "%",
        },
        height=2,
    )

    monkeypatch.setattr(
        gfs_client_module.cfgrib,
        "open_datasets",
        lambda *args, **kwargs: [temperature_humidity],
    )

    result = GFSClient.parse_grib2(grib_file)

    assert result.source == "noaa-gfs"
    assert "t2m" in result.dataset
    assert "r2" in result.dataset