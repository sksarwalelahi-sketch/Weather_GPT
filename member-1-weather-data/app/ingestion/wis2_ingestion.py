from __future__ import annotations

from typing import Any

from app.normalization.mqtt_normalizer import MQTTWeatherNormalizer


class WIS2WeatherIngestion:
    """
    WIS2 weather-data ingestion boundary.

    The adapter accepts a WIS2 notification/message payload,
    extracts the weather observation, and passes it through
    the existing WeatherGPT validation/normalization layer.

    A live WIS2 broker/subscription can be connected later
    without changing the normalization or storage layers.
    """

    SOURCE = "wis2"

    def __init__(self, repository: Any | None = None, cache: Any | None = None):
        self.repository = repository
        self.cache = cache

    async def ingest(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise TypeError("WIS2 payload must be a JSON object")

        # Support a WIS2 notification carrying the observation
        # inside a "data" object.
        observation = payload.get("data", payload)

        if not isinstance(observation, dict):
            raise ValueError("WIS2 weather observation must be a JSON object")

        observation = dict(observation)
        observation.setdefault("source", self.SOURCE)

        weather = MQTTWeatherNormalizer.normalize(observation)

        normalized = weather.model_dump(mode="json")

        if self.repository is not None:
            await self.repository.save_mqtt_weather(weather)

        if self.cache is not None:
            cache_key = (
                f"weather:wis2:"
                f"{weather.latitude:.6f}:"
                f"{weather.longitude:.6f}"
            )

            await self.cache.set(
                cache_key,
                normalized,
                ttl=300,
            )

        return normalized