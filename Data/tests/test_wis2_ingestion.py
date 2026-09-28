import asyncio
import json

import pytest

from app.ingestion.wis2_ingestion import WIS2WeatherIngestion


class FakeMessage:
    topic = "origin/a/wis2/br-inmet/data/core/weather/synop"
    payload = json.dumps(
        {
            "id": "notification-1",
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [-99.1964, 19.404, 2314],
            },
            "properties": {
                "datetime": "2026-09-09T16:15:00Z",
            },
        }
    ).encode("utf-8")


@pytest.mark.asyncio
async def test_wis2_consumer_queues_live_notification():
    ingestion = WIS2WeatherIngestion()
    ingestion._loop = asyncio.get_running_loop()

    ingestion._on_message(None, None, FakeMessage())
    message = await ingestion.get_message(timeout=1)

    assert message["id"] == "notification-1"
    assert message["_wis2_topic"].startswith("origin/a/wis2/")
    await ingestion.disconnect()


def test_wis2_consumer_uses_verified_broker_defaults():
    ingestion = WIS2WeatherIngestion()

    assert ingestion.broker_host == "globalbroker.meteo.fr"
    assert ingestion.broker_port == 8883
    assert ingestion.username == "everyone"
    assert ingestion.topic == "origin/a/wis2/#"

