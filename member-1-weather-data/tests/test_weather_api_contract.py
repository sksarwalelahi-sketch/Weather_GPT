from datetime import datetime, timezone
from app.main import app

from fastapi.testclient import TestClient


client = TestClient(app)


def test_weather_models_contract():
    response = client.get("/weather/models")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)
    assert "models" in data
    assert isinstance(data["models"], list)

    for model in data["models"]:
        assert "id" in model
        assert "name" in model
        assert "type" in model
        assert "status" in model

        assert isinstance(model["id"], str)
        assert isinstance(model["name"], str)
        assert isinstance(model["type"], str)
        assert model["status"] in {
            "active",
            "planned",
        }


def test_gfs_endpoint_contract(monkeypatch):
    class FakeGFSService:
        def __init__(self, *args, **kwargs):
            pass

        async def get_latest(self, latitude, longitude):
            return {
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": "2026-09-04T12:00:00Z",
                "temperature": 30.5,
                "wind_speed": 12.0,
                "source": "noaa-gfs",
            }

    monkeypatch.setattr(
        "app.api.weather.GFSWeatherService",
        FakeGFSService,
    )

    response = client.get(
        "/weather/gfs",
        params={
            "latitude": 20.2961,
            "longitude": 85.8245,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["source"] == "noaa-gfs"
    assert "data" in data

    weather = data["data"]

    assert weather["latitude"] == 20.2961
    assert weather["longitude"] == 85.8245
    assert weather["temperature"] == 30.5


def test_gfs_endpoint_returns_404_when_unavailable(monkeypatch):
    class FakeGFSService:
        def __init__(self, *args, **kwargs):
            pass

        async def get_latest(self, latitude, longitude):
            return None

    monkeypatch.setattr(
        "app.api.weather.GFSWeatherService",
        FakeGFSService,
    )

    response = client.get(
        "/weather/gfs",
        params={
            "latitude": 20.2961,
            "longitude": 85.8245,
        },
    )

    assert response.status_code == 404

    data = response.json()

    assert "detail" in data


def test_era5_endpoint_contract(monkeypatch):
    async def fake_get_latest_era5(
        latitude,
        longitude,
    ):
        return {
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": "2026-09-04T12:00:00Z",
            "temperature": 28.5,
            "dewpoint": 24.0,
            "surface_pressure": 1000.0,
            "source": "era5",
        }

    monkeypatch.setattr(
        "app.api.weather.weather_repository.get_latest_era5",
        fake_get_latest_era5,
    )

    response = client.get(
        "/weather/era5",
        params={
            "latitude": 20.2961,
            "longitude": 85.8245,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["source"] == "era5"
    assert "data" in data

    weather = data["data"]

    assert weather["latitude"] == 20.2961
    assert weather["longitude"] == 85.8245
    assert weather["temperature"] == 28.5
    assert weather["source"] == "era5"


def test_era5_endpoint_returns_404_when_unavailable(monkeypatch):
    async def fake_get_latest_era5(
        latitude,
        longitude,
    ):
        return None

    monkeypatch.setattr(
        "app.api.weather.weather_repository.get_latest_era5",
        fake_get_latest_era5,
    )

    response = client.get(
        "/weather/era5",
        params={
            "latitude": 20.2961,
            "longitude": 85.8245,
        },
    )

    assert response.status_code == 404

    data = response.json()

    assert "detail" in data


def test_gfs_endpoint_rejects_invalid_coordinates():
    response = client.get(
        "/weather/gfs",
        params={
            "latitude": 100,
            "longitude": 85.8245,
        },
    )

    assert response.status_code == 422


def test_era5_endpoint_rejects_invalid_coordinates():
    response = client.get(
        "/weather/era5",
        params={
            "latitude": 20.2961,
            "longitude": 200,
        },
    )

    assert response.status_code == 422