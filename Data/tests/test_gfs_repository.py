from datetime import datetime, timezone

import pytest

from app.gfs.normalizer import GFSPointWeather
from app.repositories.weather_repository import (
    MongoWeatherRepository,
)


class FakeInsertResult:
    inserted_id = "gfs-test-id"


class FakeCollection:
    def __init__(self):
        self.documents = []
        self.indexes = []

    async def insert_one(self, document):
        self.documents.append(document)
        return FakeInsertResult()

    async def create_index(self, index):
        self.indexes.append(index)
        return "index-created"


class FakeDatabase:
    def __init__(self):
        self.database = object()
        self.collections = {}

    async def connect(self):
        self.database = object()

    def get_database(self):
        return FakeDatabaseHandle(
            self.collections
        )


class FakeDatabaseHandle:
    def __init__(self, collections):
        self.collections = collections

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = FakeCollection()

        return self.collections[name]


def make_gfs_weather():
    return GFSPointWeather(
        latitude=20.2961,
        longitude=85.8245,
        valid_at=datetime(
            2026,
            8,
            30,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        temperature=300.15,
        relative_humidity=75.0,
        surface_pressure=100500.0,
        wind_speed=5.0,
        wind_direction=216.87,
        precipitation=2.5,
        source="noaa-gfs",
    )


@pytest.mark.asyncio
async def test_save_gfs():
    database = FakeDatabase()

    repository = MongoWeatherRepository(
        database
    )

    weather = make_gfs_weather()

    result = await repository.save_gfs(
        weather
    )

    assert result == "gfs-test-id"

    collection = database.collections[
        repository.GFS_COLLECTION
    ]

    assert len(collection.documents) == 1

    document = collection.documents[0]

    assert document["latitude"] == 20.2961
    assert document["longitude"] == 85.8245
    assert document["temperature"] == 300.15
    assert document["relative_humidity"] == 75.0
    assert document["surface_pressure"] == 100500.0
    assert document["wind_speed"] == 5.0
    assert document["wind_direction"] == pytest.approx(
        216.87,
        abs=0.01,
    )
    assert document["precipitation"] == 2.5
    assert document["source"] == "noaa-gfs"

    assert "valid_at" in document
    assert "updated_at" in document


@pytest.mark.asyncio
async def test_gfs_collection_name():
    database = FakeDatabase()

    repository = MongoWeatherRepository(
        database
    )

    assert (
        repository.GFS_COLLECTION
        == "gfs_weather"
    )


@pytest.mark.asyncio
async def test_create_gfs_indexes():
    database = FakeDatabase()

    repository = MongoWeatherRepository(
        database
    )

    await repository.create_indexes()

    collection = database.collections[
        repository.GFS_COLLECTION
    ]

    assert len(collection.indexes) == 2