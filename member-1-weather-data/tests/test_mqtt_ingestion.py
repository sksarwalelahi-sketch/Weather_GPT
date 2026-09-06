import asyncio
import json

import paho.mqtt.client as mqtt

from app.ingestion.mqtt_ingestion import MQTTWeatherIngestion


BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
TOPIC = "weathergpt/weather"


async def main():
    ingestion = MQTTWeatherIngestion(
        broker_host=BROKER_HOST,
        broker_port=BROKER_PORT,
        topic=TOPIC,
    )

    publisher = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="weathergpt-test-publisher",
    )

    try:
        print("Connecting MQTT ingestion...")
        await ingestion.connect()

        await asyncio.sleep(1)

        publisher.connect(
            BROKER_HOST,
            BROKER_PORT,
            60,
        )

        publisher.loop_start()

        payload = {
            "latitude": 20.2961,
            "longitude": 85.8245,
            "temperature": 28.4,
            "relative_humidity": 78.0,
            "wind_speed": 12.5,
            "wind_direction": 240.0,
            "precipitation": 0.2,
            "source": "mqtt-test",
        }

        print("Publishing test weather message...")

        result = publisher.publish(
            TOPIC,
            json.dumps(payload),
        )

        result.wait_for_publish()

        message = await ingestion.get_message(
            timeout=10
        )

        print("MQTT MESSAGE RECEIVED")
        print("Latitude:", message.get("latitude"))
        print("Longitude:", message.get("longitude"))
        print("Temperature:", message.get("temperature"))
        print(
            "Relative Humidity:",
            message.get("relative_humidity"),
        )
        print("Wind Speed:", message.get("wind_speed"))
        print(
            "Wind Direction:",
            message.get("wind_direction"),
        )
        print(
            "Precipitation:",
            message.get("precipitation"),
        )
        print("Source:", message.get("source"))

    finally:
        publisher.loop_stop()

        if publisher.is_connected():
            publisher.disconnect()

        await ingestion.disconnect()


if __name__ == "__main__":
    asyncio.run(main())