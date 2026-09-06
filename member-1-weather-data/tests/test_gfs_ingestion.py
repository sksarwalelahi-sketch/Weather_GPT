import numpy as np
import pytest
import xarray as xr

from app.gfs.client import GFSData
from app.gfs.ingestion import GFSIngestion


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


class FakeClient:
    def __init__(self, dataset):
        self.dataset = dataset
        self.closed = False

    def parse_grib2(self, file_path):
        return GFSData(
            dataset=self.dataset,
        )

    async def get_grib2(
        self,
        url,
        output_path,
    ):
        return GFSData(
            dataset=self.dataset,
        )

    async def close(self):
        self.closed = True


class FakeRepository:
    def __init__(self):
        self.saved = []

    async def save_gfs(self, weather):
        self.saved.append(weather)
        return "gfs-id"


def test_gfs_ingestion_initialization():
    client = FakeClient(
        make_gfs_dataset()
    )

    ingestion = GFSIngestion(
        client=client,
    )

    assert ingestion.client is client
    assert ingestion.repository is None
    assert ingestion.SOURCE == "noaa-gfs"


def test_gfs_point_validation():
    client = FakeClient(
        make_gfs_dataset()
    )

    ingestion = GFSIngestion(
        client=client,
    )

    weather = ingestion.normalize_and_validate(
        dataset=make_gfs_dataset(),
        latitude=20.2961,
        longitude=85.8245,
    )

    assert weather.temperature == pytest.approx(
        300.15
    )

    assert weather.relative_humidity == pytest.approx(
        75.0
    )

    assert weather.surface_pressure == pytest.approx(
        100500.0
    )

    assert weather.wind_speed == pytest.approx(
        5.0
    )


def test_invalid_gfs_humidity_is_rejected():
    dataset = make_gfs_dataset()

    dataset["r2"] = (
        ("latitude", "longitude"),
        np.array([[150.0]]),
    )

    ingestion = GFSIngestion(
        client=FakeClient(dataset)
    )

    with pytest.raises(ValueError):
        ingestion.normalize_and_validate(
            dataset=dataset,
            latitude=20.2961,
            longitude=85.8245,
        )


@pytest.mark.asyncio
async def test_ingest_data():
    repository = FakeRepository()

    ingestion = GFSIngestion(
        client=FakeClient(
            make_gfs_dataset()
        ),
        repository=repository,
    )

    data = GFSData(
        dataset=make_gfs_dataset()
    )

    result = await ingestion.ingest_data(
        data=data,
        latitude=20.2961,
        longitude=85.8245,
    )

    assert result.source == "noaa-gfs"
    assert result.temperature == pytest.approx(
        300.15
    )

    assert len(repository.saved) == 1
    assert repository.saved[0] == result


@pytest.mark.asyncio
async def test_ingest_grib2():
    repository = FakeRepository()

    ingestion = GFSIngestion(
        client=FakeClient(
            make_gfs_dataset()
        ),
        repository=repository,
    )

    result = await ingestion.ingest_grib2(
        file_path="sample.grib2",
        latitude=20.2961,
        longitude=85.8245,
    )

    assert result.source == "noaa-gfs"
    assert len(repository.saved) == 1


@pytest.mark.asyncio
async def test_ingest_remote():
    repository = FakeRepository()

    ingestion = GFSIngestion(
        client=FakeClient(
            make_gfs_dataset()
        ),
        repository=repository,
    )

    result = await ingestion.ingest_remote(
        url="https://example.com/sample.grib2",
        output_path="sample.grib2",
        latitude=20.2961,
        longitude=85.8245,
    )

    assert result.source == "noaa-gfs"
    assert len(repository.saved) == 1


@pytest.mark.asyncio
async def test_close():
    client = FakeClient(
        make_gfs_dataset()
    )

    ingestion = GFSIngestion(
        client=client,
    )

    await ingestion.close()

    assert client.closed is True