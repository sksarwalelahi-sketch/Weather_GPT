from __future__ import annotations

from typing import Any

import httpx

from app.normalization.imd_normalizer import (
    IMDWeatherNormalizer,
)


class IMDClient:
    """
    Client boundary for an official IMD weather feed.

    No endpoint is hard-coded because the project does not
    currently specify a verified official IMD API/feed URL.
    """

    SOURCE = "imd"

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            timeout=timeout
        )

    async def get_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:

        if not self.base_url:
            raise RuntimeError(
                "IMD data source is not configured. "
                "Set the official IMD API/feed endpoint "
                "before requesting live IMD weather data."
            )

        response = await self.client.get(
            self.base_url,
            params={
                "latitude": latitude,
                "longitude": longitude,
            },
        )

        response.raise_for_status()

        data = response.json()

        return {
            "source": self.SOURCE,
            "latitude": latitude,
            "longitude": longitude,
            "data": data,
        }

    async def close(self):
        await self.client.aclose()


class IMDIngestion:
    """
    IMD ingestion + normalization + optional persistence.
    """

    SOURCE = "imd"

    CACHE_TTL = 300

    def __init__(
        self,
        client: IMDClient | None = None,
        repository: Any | None = None,
        cache: Any | None = None,
    ):
        self.client = client or IMDClient()
        self.repository = repository
        self.cache = cache

    async def ingest_weather(
        self,
        latitude: float,
        longitude: float,
    ):
        payload = await self.client.get_weather(
            latitude,
            longitude,
        )

        observation = payload.get(
            "data",
            payload,
        )

        if isinstance(observation, dict):
            observation = dict(observation)

            observation.setdefault(
                "latitude",
                latitude,
            )

            observation.setdefault(
                "longitude",
                longitude,
            )

        normalized = IMDWeatherNormalizer.normalize(
            observation
        )

        if self.repository is not None:
            await self.repository.save_imd_weather(
                normalized
            )

        if self.cache is not None:
            cache_key = (
                f"weather:imd:"
                f"{normalized.latitude:.6f}:"
                f"{normalized.longitude:.6f}"
            )

            await self.cache.set(
                cache_key,
                normalized.model_dump(
                    mode="json"
                ),
                ttl=self.CACHE_TTL,
            )

        return normalized

    async def close(self):
        await self.client.close()