from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.dependencies import redis_cache, weather_repository
from app.services.weather_service import WeatherService


router = APIRouter(tags=["Live updates"])


class LiveUpdateManager:
    """Tracks WebSocket subscribers and publishes typed live updates."""

    def __init__(self) -> None:
        self._channels: dict[str, set[asyncio.Queue[dict[str, Any]]]] = (
            defaultdict(set)
        )

    async def subscribe(
        self,
        channel: str,
    ) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._channels[channel].add(queue)
        return queue

    async def unsubscribe(
        self,
        channel: str,
        queue: asyncio.Queue[dict[str, Any]],
    ) -> None:
        subscribers = self._channels[channel]
        subscribers.discard(queue)
        if not subscribers:
            self._channels.pop(channel, None)

    async def publish(
        self,
        channel: str,
        payload: dict[str, Any],
    ) -> None:
        for queue in tuple(self._channels.get(channel, ())):
            await queue.put(payload)


live_updates = LiveUpdateManager()


@router.websocket("/ws/weather")
async def weather_updates(
    websocket: WebSocket,
    latitude: float,
    longitude: float,
    interval: int = 60,
) -> None:
    await websocket.accept()
    interval = max(10, min(interval, 900))
    service = WeatherService(
        repository=weather_repository,
        cache=redis_cache,
    )

    try:
        while True:
            weather = await service.get_current_weather(
                latitude=latitude,
                longitude=longitude,
            )
            await websocket.send_json(
                {
                    "type": "weather",
                    "data": weather.model_dump(mode="json"),
                }
            )
            await asyncio.sleep(interval)
    except WebSocketDisconnect:
        pass
    finally:
        await service.close()


async def _event_updates(
    websocket: WebSocket,
    channel: str,
    event_type: str,
) -> None:
    await websocket.accept()
    queue = await live_updates.subscribe(channel)

    try:
        await websocket.send_json(
            {
                "type": "connected",
                "channel": channel,
            }
        )
        while True:
            payload = await queue.get()
            await websocket.send_json(
                {
                    "type": event_type,
                    "data": payload,
                }
            )
    except WebSocketDisconnect:
        pass
    finally:
        await live_updates.unsubscribe(channel, queue)


@router.websocket("/ws/alerts")
async def alert_updates(websocket: WebSocket) -> None:
    """Stream alert events published to the ``alerts`` channel."""
    await _event_updates(websocket, "alerts", "alert")


@router.websocket("/ws/map")
async def map_updates(websocket: WebSocket) -> None:
    """Stream map-layer events published to the ``map`` channel."""
    await _event_updates(websocket, "map", "map")
