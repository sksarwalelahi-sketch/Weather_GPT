import pytest

from app.ingestion.satellite_ingestion import (
    MOSDACClient,
    SatelliteWeatherIngestion,
)


class FakeRepository:
    def __init__(self):
        self.saved = []

    async def save_satellite_weather(
        self,
        weather,
    ):
        self.saved.append(weather)
        return "test-id"


class FakeCache:
    def __init__(self):
        self.values = {}

    async def set(
        self,
        key,
        value,
        ttl=None,
    ):
        self.values[key] = {
            "value": value,
            "ttl": ttl,
        }

        return True


@pytest.mark.asyncio
async def test_satellite_ingestion_pipeline():
    repository = FakeRepository()
    cache = FakeCache()

    ingestion = SatelliteWeatherIngestion(
        repository=repository,
        cache=cache,
    )

    payload = {
        "data": {
            "lat": 20.2961,
            "lon": 85.8245,
            "time": "2026-09-04T10:00:00Z",
            "cloud": 72.0,
            "brightness_temp": 248.3,
            "rainfall": 0.8,
            "solar": 510.0,
        },
        "product": "INSAT-test",
    }

    result = await ingestion.ingest(
        payload
    )

    assert result["latitude"] == 20.2961
    assert result["longitude"] == 85.8245
    assert result["cloud_cover"] == 72.0
    assert result["brightness_temperature"] == 248.3
    assert result["rainfall_estimate"] == 0.8
    assert result["solar_radiation"] == 510.0

    assert len(repository.saved) == 1
    assert len(cache.values) == 1


@pytest.mark.asyncio
async def test_satellite_ingestion_rejects_invalid_payload():
    ingestion = SatelliteWeatherIngestion()

    with pytest.raises(TypeError):
        await ingestion.ingest(
            "invalid"
        )


@pytest.mark.asyncio
async def test_mosdac_catalog_matches_live_payload_shape(monkeypatch):
    client = MOSDACClient(
        base_url="https://mosdac.gov.in/apios/datasets.json"
    )

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "updated": "2026-09-09T16:15:00Z",
                "totalResults": 164928,
                "entries": [
                    {
                        "identifier": (
                            "3RIMG_09SEP2026_1615_L2B_SST_V02R00.h5"
                        ),
                        "id": "18386944",
                        "updated": "2026-09-09T16:15:00Z",
                        "enclosureLink": (
                            "https://mosdac.gov.in/uops/?metaid=18386944"
                        ),
                        "boundbox": [
                            {
                                "west": "-7.15",
                                "south": "-81.04",
                                "east": "155.15",
                                "north": "81.04",
                            }
                        ],
                    }
                ],
            }

    async def fake_get(url, params):
        assert params == {
            "datasetId": "3RIMG_L2B_SST",
            "count": 1,
        }
        return FakeResponse()

    monkeypatch.setattr(client.client, "get", fake_get)
    payload = await client.get_latest_catalog()

    assert payload["entries"][0]["identifier"].endswith(".h5")
    assert payload["entries"][0]["enclosureLink"].startswith(
        "https://mosdac.gov.in/"
    )
    await client.close()