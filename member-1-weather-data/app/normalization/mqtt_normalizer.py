from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.mqtt_weather import MQTTWeather


class MQTTWeatherNormalizer:
    """
    Validates and normalizes raw MQTT weather messages
    into the WeatherGPT MQTTWeather model.
    """

    SOURCE = "mqtt"

    @staticmethod
    def normalize(payload: dict[str, Any]) -> MQTTWeather:
        if not isinstance(payload, dict):
            raise TypeError("MQTT weather payload must be a dictionary")

        data = dict(payload)

        # MQTT messages may identify their source explicitly.
        data.setdefault("source", MQTTWeatherNormalizer.SOURCE)

        # Accept common timestamp field names.
        if "timestamp" not in data:
            if "observed_at" in data:
                data["timestamp"] = data["observed_at"]
            elif "time" in data:
                data["timestamp"] = data["time"]
            else:
                # If the sensor does not provide a timestamp,
                # use the ingestion time.
                data["timestamp"] = datetime.now(timezone.utc)

        # Accept common MQTT field aliases.
        aliases = {
            "lat": "latitude",
            "lon": "longitude",
            "temp": "temperature",
            "humidity": "relative_humidity",
            "wind": "wind_speed",
            "wind_direction_10m": "wind_direction",
            "rain": "precipitation",
        }

        for source_field, target_field in aliases.items():
            if target_field not in data and source_field in data:
                data[target_field] = data[source_field]

        weather = MQTTWeather.model_validate(data)

        return weather
    