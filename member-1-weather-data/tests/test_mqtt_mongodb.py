import asyncio
import json

import paho.mqtt.client as mqtt

from app.core.dependencies import weather_repository
from app.database.mongodb import mongodb
from app.ingestion.mqtt_ingestion import MQTTWeatherIngestion


BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
TOPIC = "weathergpt/weather"

LATITUDE = 20.2961
LONGITUDE = 85.8245


async def main():
    await mongodb.connect()

    ingestion = MQTTWeatherIngestion(
        broker_host=BROKER_HOST,
        broker_port=BROKER_PORT,
        topic=TOPIC,
        repository=weather_repository,
    )

    publisher = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="weathergpt-mongodb-test",
    )

    try:
        await ingestion.connect()
        await asyncio.sleep(1)

        publisher.connect(
            BROKER_HOST,
            BROKER_PORT,
            60,
        )

        publisher.loop_start()

        payload = {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "temperature": 29.1,
            "relative_humidity": 76.0,
            "wind_speed": 10.5,
            "wind_direction": 235.0,
            "precipitation": 0.1,
            "source": "mqtt-mongodb-test",
        }

        print("Publishing MQTT weather message...")

        result = publisher.publish(
            TOPIC,
            json.dumps(payload),
        )

        result.wait_for_publish()

        message = await ingestion.get_message(
            timeout=10
        )

        print("\nMQTT NORMALIZED MESSAGE")
        print(message)

        # Give the background persistence coroutine
        # enough time to complete.
        await asyncio.sleep(1)

        database = mongodb.get_database()

        saved = await database["mqtt_weather"].find_one(
            {
                "latitude": LATITUDE,
                "longitude": LONGITUDE,
                "source": "mqtt-mongodb-test",
            },
            sort=[("updated_at", -1)],
        )

        print("\nMONGODB SAVED DOCUMENT")
        print(saved)

        if saved is None:
            raise RuntimeError(
                "MQTT weather document was not found in MongoDB"
            )

        print("\nMQTT → MongoDB persistence SUCCESS")

    finally:
        publisher.loop_stop()

        if publisher.is_connected():
            publisher.disconnect()

        await ingestion.disconnect()
        await mongodb.disconnect()


if __name__ == "__main__":
    asyncio.run(main())