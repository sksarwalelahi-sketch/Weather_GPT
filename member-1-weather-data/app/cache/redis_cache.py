from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis


class RedisWeatherCache:
    """
    Redis cache for the Member 1 weather-data platform.

    Redis is used as a fast cache in front of the weather data layer.
    MongoDB remains the persistent weather-data store.

    The cache is intentionally independent from the weather service so
    it can be tested and replaced without changing the ingestion layer.
    """

    DEFAULT_HOST = "127.0.0.1"
    DEFAULT_PORT = 6379

    CURRENT_TTL = 300
    FORECAST_TTL = 900
    HISTORICAL_TTL = 3600
    GFS_TTL = 1800

    KEY_PREFIX = "weather"

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        db: int = 0,
        default_ttl: int = CURRENT_TTL,
    ):
        if not host:
            raise ValueError("host must not be empty")

        if port < 1 or port > 65535:
            raise ValueError(
                "port must be between 1 and 65535"
            )

        if db < 0:
            raise ValueError(
                "db must be greater than or equal to 0"
            )

        if default_ttl < 1:
            raise ValueError(
                "default_ttl must be greater than 0"
            )

        self.host = host
        self.port = port
        self.db = db
        self.default_ttl = default_ttl

        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
        )

    @classmethod
    def current_key(
        cls,
        latitude: float,
        longitude: float,
    ) -> str:
        return (
            f"{cls.KEY_PREFIX}:current:"
            f"{latitude:.6f}:"
            f"{longitude:.6f}"
        )

    @classmethod
    def forecast_key(
        cls,
        latitude: float,
        longitude: float,
    ) -> str:
        return (
            f"{cls.KEY_PREFIX}:forecast:"
            f"{latitude:.6f}:"
            f"{longitude:.6f}"
        )

    @classmethod
    def historical_key(
        cls,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
    ) -> str:
        return (
            f"{cls.KEY_PREFIX}:historical:"
            f"{latitude:.6f}:"
            f"{longitude:.6f}:"
            f"{start_date}:"
            f"{end_date}"
        )

    @classmethod
    def gfs_key(
        cls,
        latitude: float,
        longitude: float,
        valid_at: str,
    ) -> str:
        return (
            f"{cls.KEY_PREFIX}:gfs:"
            f"{latitude:.6f}:"
            f"{longitude:.6f}:"
            f"{valid_at}"
        )

    async def get(
        self,
        key: str,
    ) -> dict[str, Any] | list[Any] | None:
        if not key:
            raise ValueError("key must not be empty")

        value = await self.client.get(key)

        if value is None:
            return None

        return json.loads(value)

    async def set(
        self,
        key: str,
        value: dict[str, Any] | list[Any],
        ttl: int | None = None,
    ) -> bool:
        if not key:
            raise ValueError("key must not be empty")

        cache_ttl = (
            self.default_ttl
            if ttl is None
            else ttl
        )

        if cache_ttl < 1:
            raise ValueError(
                "ttl must be greater than 0"
            )

        serialized = json.dumps(
            value,
            default=str,
        )

        return bool(
            await self.client.set(
                key,
                serialized,
                ex=cache_ttl,
            )
        )

    async def delete(
        self,
        key: str,
    ) -> bool:
        if not key:
            raise ValueError("key must not be empty")

        deleted = await self.client.delete(key)

        return deleted > 0

    async def exists(
        self,
        key: str,
    ) -> bool:
        if not key:
            raise ValueError("key must not be empty")

        return bool(
            await self.client.exists(key)
        )

    async def clear_weather_cache(self) -> None:
        """
        Remove weather cache entries created by this application.

        This is intended for development/testing and controlled
        cache invalidation.
        """

        pattern = f"{self.KEY_PREFIX}:*"

        keys = []

        async for key in self.client.scan_iter(
            match=pattern,
        ):
            keys.append(key)

        if keys:
            await self.client.delete(*keys)

    async def ping(self) -> bool:
        return bool(await self.client.ping())

    async def close(self) -> None:
        await self.client.aclose()