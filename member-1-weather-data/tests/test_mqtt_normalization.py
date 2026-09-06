import asyncio
import json

import paho.mqtt.client as mqtt

from app.ingestion.mqtt_ingestion import MQTTWeatherIngestion


async def main():
    ingestion = MQTTWeatherIngestion()

    await ingestion.connect()

    publisher = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2
    )

    publisher.connect("127.0.0.1", 1883, 60)
    publisher.loop_start()

    payload = {
        "latitude": 20.2961,
        "longitude": 85.8245,
        "temperature": 28.4,
        "relative_humidity": 78,
        "wind_speed": 12.5,
        "wind_direction": 240,
        "precipitation": 0.2,
        "source": "mqtt-test",
    }

    publisher.publish(
        "weathergpt/weather",
        json.dumps(payload),
    )

    message = await ingestion.get_message(timeout=5)

    print("\nNORMALIZED MQTT MESSAGE")
    print(message)

    publisher.loop_stop()
    publisher.disconnect()

    await ingestion.disconnect()


if __name__ == "__main__":
    asyncio.run(main())