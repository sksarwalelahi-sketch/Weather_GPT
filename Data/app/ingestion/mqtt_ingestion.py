from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

import paho.mqtt.client as mqtt

from app.normalization.mqtt_normalizer import MQTTWeatherNormalizer


class MQTTWeatherIngestion:
    """
    Receives weather observations from an MQTT broker,
    normalizes and validates them, and optionally persists
    them to MongoDB and Redis.
    """

    SOURCE = "mqtt"
    CACHE_TTL = 300

    def __init__(
        self,
        broker_host: str = "127.0.0.1",
        broker_port: int = 1883,
        topic: str = "weathergpt/weather",
        callback: Callable[[dict[str, Any]], Any] | None = None,
        repository: Any | None = None,
        cache: Any | None = None,
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        self.callback = callback

        self.repository = repository
        self.cache = cache

        self.queue: asyncio.Queue = asyncio.Queue()

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="weathergpt-ingestion",
        )

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        self._loop: asyncio.AbstractEventLoop | None = None

    @staticmethod
    def _cache_key(latitude: float, longitude: float) -> str:
        return (
            f"weather:mqtt:"
            f"{latitude:.6f}:"
            f"{longitude:.6f}"
        )

    def _on_connect(
        self,
        client,
        userdata,
        flags,
        reason_code,
        properties,
    ):
        if reason_code == 0:
            client.subscribe(self.topic)

            print(
                f"MQTT connected: "
                f"{self.broker_host}:{self.broker_port}"
            )
            print(f"Subscribed to: {self.topic}")

        else:
            print(
                f"MQTT connection failed: "
                f"{reason_code}"
            )

    def _on_message(
        self,
        client,
        userdata,
        message,
    ):
        try:
            payload = json.loads(
                message.payload.decode("utf-8")
            )

            if not isinstance(payload, dict):
                raise ValueError(
                    "MQTT weather payload must be a JSON object"
                )

            payload.setdefault(
                "source",
                self.SOURCE,
            )

            weather = MQTTWeatherNormalizer.normalize(
                payload
            )

            normalized_payload = weather.model_dump(
                mode="json"
            )

            if self._loop is not None:
                self._loop.call_soon_threadsafe(
                    self.queue.put_nowait,
                    normalized_payload,
                )

            if self.callback is not None:
                result = self.callback(
                    normalized_payload
                )

                if (
                    asyncio.iscoroutine(result)
                    and self._loop is not None
                ):
                    asyncio.run_coroutine_threadsafe(
                        result,
                        self._loop,
                    )

            if (
                self.repository is not None
                and self._loop is not None
            ):
                asyncio.run_coroutine_threadsafe(
                    self.repository.save_mqtt_weather(
                        weather
                    ),
                    self._loop,
                )

            if (
                self.cache is not None
                and self._loop is not None
            ):
                cache_key = self._cache_key(
                    weather.latitude,
                    weather.longitude,
                )

                asyncio.run_coroutine_threadsafe(
                    self.cache.set(
                        cache_key,
                        normalized_payload,
                        ttl=self.CACHE_TTL,
                    ),
                    self._loop,
                )

        except Exception as exc:
            print(
                f"MQTT message processing failed: "
                f"{exc}"
            )

    async def connect(self):
        self._loop = asyncio.get_running_loop()

        await asyncio.to_thread(
            self.client.connect,
            self.broker_host,
            self.broker_port,
            60,
        )

        self.client.loop_start()

    async def get_message(
        self,
        timeout=None,
    ):
        if timeout is None:
            return await self.queue.get()

        return await asyncio.wait_for(
            self.queue.get(),
            timeout=timeout,
        )

    async def disconnect(self):
        try:
            self.client.loop_stop()

            if self.client.is_connected():
                await asyncio.to_thread(
                    self.client.disconnect
                )

        finally:
            self._loop = None