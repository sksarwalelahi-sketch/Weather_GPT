from __future__ import annotations

from typing import Any

from app.normalization.satellite_normalizer import (
    SatelliteWeatherNormalizer,
)


class SatelliteWeatherIngestion:
    """
    Provider-neutral satellite ingestion boundary.

    Actual MOSDAC/INSAT transport can be connected
    later without changing normalization or storage.
    """

    SOURCE = "mosdac"

    CACHE_TTL = 900

    def __init__(
        self,
        repository: Any | None = None,
        cache: Any | None = None,
    ):
        self.repository = repository
        self.cache = cache

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