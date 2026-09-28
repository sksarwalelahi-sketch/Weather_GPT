from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.normalization.satellite_normalizer import (
    SatelliteWeatherNormalizer,
)


class MOSDACClient:
    """HTTP boundary for a configured MOSDAC/INSAT data feed."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url or settings.MOSDAC_API_URL
        self.client = httpx.AsyncClient(timeout=timeout)

    async def get_observation(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        if not self.base_url:
            raise RuntimeError(
                "MOSDAC data source is not configured. "
                "Set MOSDAC_API_URL before requesting live satellite data."
            )

        response = await self.client.get(
            self.base_url,
            params={
                "latitude": latitude,
                "longitude": longitude,
            },
        )

        response.raise_for_status()

        return response.json()

    async def get_latest_catalog(
        self,
        count: int = 1,
    ) -> dict[str, Any]:
        """Fetch live INSAT granule metadata from MOSDAC OpenSearch."""
        catalog_url = self.base_url or settings.MOSDAC_CATALOG_URL
        if not catalog_url:
            raise RuntimeError(
                "MOSDAC data source is not configured. "
                "Set MOSDAC_CATALOG_URL before requesting live satellite data."
            )

        response = await self.client.get(
            catalog_url,
            params={
                "datasetId": settings.MOSDAC_DATASET_ID,
                "count": count,
            },
        )
        response.raise_for_status()
        payload = response.json()

        if not isinstance(payload, dict):
            raise TypeError(
                "MOSDAC catalog payload must be a dictionary"
            )

        return payload

    async def close(self) -> None:
        await self.client.aclose()


class SatelliteWeatherIngestion:
    """
    Provider-neutral satellite ingestion boundary.

    The MOSDAC/INSAT transport is configurable through MOSDAC_API_URL.
    """

    SOURCE = "mosdac"

    CACHE_TTL = 900

    def __init__(
        self,
        repository: Any | None = None,
        cache: Any | None = None,
        client: MOSDACClient | None = None,
    ):
        self.repository = repository
        self.cache = cache
        self.client = client

    async def ingest_live(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        """Fetch a configured satellite observation and run the normal pipeline."""

        if self.client is None:
            self.client = MOSDACClient()

        payload = await self.client.get_observation(
            latitude,
            longitude,
        )

        return await self.ingest(payload)

    async def ingest(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:

        if not isinstance(payload, dict):
            raise TypeError(
                "Satellite payload must be a dictionary"
            )

        observation = payload.get(
            "data",
            payload,
        )

        if not isinstance(observation, dict):
            raise ValueError(
                "Satellite data must be a dictionary"
            )

        observation = dict(observation)

        observation.setdefault(
            "source",
            self.SOURCE,
        )

        # Preserve product metadata from the
        # outer payload when available.
        if (
            "product" in payload
            and "product" not in observation
        ):
            observation["product"] = payload[
                "product"
            ]

        weather = (
            SatelliteWeatherNormalizer.normalize(
                observation
            )
        )

        normalized = weather.model_dump(
            mode="json"
        )

        # Persist to MongoDB.
        if self.repository is not None:
            await self.repository.save_satellite_weather(
                weather
            )

        # Cache normalized observation.
        if self.cache is not None:
            cache_key = (
                "weather:satellite:"
                f"{weather.latitude:.6f}:"
                f"{weather.longitude:.6f}"
            )

            await self.cache.set(
                cache_key,
                normalized,
                ttl=self.CACHE_TTL,
            )

        return normalized

    async def close(self) -> None:
        if self.client is not None:
            await self.client.close()
