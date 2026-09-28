from __future__ import annotations

import asyncio
import json
from typing import Any

import paho.mqtt.client as mqtt

from app.core.config import settings
from app.normalization.mqtt_normalizer import MQTTWeatherNormalizer


class WIS2WeatherIngestion:
    """
    WIS2 weather-data ingestion boundary.

    The adapter accepts a WIS2 notification/message payload,
    extracts the weather observation, and passes it through
    the existing WeatherGPT validation/normalization layer.

    The consumer connects to a WIS2 Global Broker over MQTTS and queues
    notification messages. Observation payloads can still be passed directly
    to ``ingest`` for normalization and persistence.
    """

    SOURCE = "wis2"

    def __init__(
        self,
        repository: Any | None = None,
        cache: Any | None = None,
        broker_host: str = settings.WIS2_BROKER_HOST,
        broker_port: int = settings.WIS2_BROKER_PORT,
        username: str = settings.WIS2_BROKER_USERNAME,
        password: str = settings.WIS2_BROKER_PASSWORD,
        topic: str = settings.WIS2_TOPIC,
    ):
        self.repository = repository
        self.cache = cache
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.topic = topic
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._connected = asyncio.Event()

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="weathergpt-wis2-consumer",
        )
        self.client.username_pw_set(username, password)
        self.client.tls_set()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(
        self,
        client,
        userdata,
        flags,
        reason_code,
        properties,
    ) -> None:
        if reason_code != 0:
            return

        client.subscribe(self.topic)
        if self._loop is not None:
            self._loop.call_soon_threadsafe(
                self._connected.set
            )

    def _on_message(self, client, userdata, message) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError(
                    "WIS2 broker message must be a JSON object"
                )
            payload["_wis2_topic"] = message.topic
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return

        if self._loop is not None:
            self._loop.call_soon_threadsafe(
                self.queue.put_nowait,
                payload,
            )

    async def connect(self, timeout: float = 30.0) -> None:
        self._loop = asyncio.get_running_loop()
        await asyncio.to_thread(
            self.client.connect,
            self.broker_host,
            self.broker_port,
            60,
        )
        self.client.loop_start()
        try:
            await asyncio.wait_for(
                self._connected.wait(),
                timeout=timeout,
            )
        except TimeoutError as exc:
            await self.disconnect()
            raise RuntimeError(
                "WIS2 broker connection timed out"
            ) from exc

    async def get_message(
        self,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        if timeout is None:
            return await self.queue.get()
        return await asyncio.wait_for(
            self.queue.get(),
            timeout=timeout,
        )

    async def disconnect(self) -> None:
        self.client.loop_stop()
        if self.client.is_connected():
            await asyncio.to_thread(self.client.disconnect)
        self._loop = None
        self._connected.clear()

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