import asyncio
import json

import paho.mqtt.client as mqtt

from app.core.dependencies import redis_cache, weather_repository
from app.database.mongodb import mongodb
from app.ingestion.mqtt_ingestion import MQTTWeatherIngestion


BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
TOPIC = "weathergpt/weather"

LATITUDE = 20.2961
LONGITUDE = 85.8245

CACHE_KEY = (
    f"weather:mqtt:"
    f"{LATITUDE:.6f}:"
    f"{LONGITUDE:.6f}"
)


async def main():
    await mongodb.connect()

    ingestion = MQTTWeatherIngestion(
        broker_host=BROKER_HOST,
        broker_port=BROKER_PORT,
        topic=TOPIC,
        repository=weather_repository,
        cache=redis_cache,
    )

    publisher = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="weathergpt-full-pipeline-test",
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
            "temperature": 30.2,
            "relative_humidity": 74.0,
            "wind_speed": 11.5,
            "wind_direction": 238.0,
            "precipitation": 0.3,
            "source": "mqtt-full-pipeline-test",
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

        print("\n1. MQTT NORMALIZED MESSAGE")
        print(message)

        # Allow asynchronous MongoDB and Redis
        # persistence operations to finish.
        await asyncio.sleep(1)

        database = mongodb.get_database()

        saved = await database[
            "mqtt_weather"
        ].find_one(
            {
                "latitude": LATITUDE,
                "longitude": LONGITUDE,
                "source": "mqtt-full-pipeline-test",
            },
            sort=[("updated_at", -1)],
        )

        cached = await redis_cache.get(
            CACHE_KEY
        )

        print("\n2. MONGODB DOCUMENT")
        print(saved)

        print("\n3. REDIS CACHE")
        print(cached)

        if saved is None:
            raise RuntimeError(
                "MQTT document was not saved to MongoDB"
            )

        if cached is None:
            raise RuntimeError(
                "MQTT observation was not cached in Redis"
            )

        print(
            "\nMQTT → Normalize → "
            "MongoDB + Redis SUCCESS"
        )

    finally:
        publisher.loop_stop()

        if publisher.is_connected():
            publisher.disconnect()

        await ingestion.disconnect()

        # Remove the temporary cache entry.
        await redis_cache.delete(CACHE_KEY)

        await mongodb.disconnect()


if __name__ == "__main__":
    asyncio.run(main())