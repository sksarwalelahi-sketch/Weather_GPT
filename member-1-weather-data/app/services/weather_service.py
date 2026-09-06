from __future__ import annotations

from typing import Any

from app.cache.redis_cache import RedisWeatherCache
from app.normalization.weather_normalizer import (
    CanonicalForecast,
    CanonicalHistorical,
    CanonicalWeather,
    WeatherNormalizer,
)
from app.openmeteo.client import OpenMeteoClient
from app.repositories.weather_repository import WeatherRepository


class WeatherService:
    def __init__(
        self,
        client: OpenMeteoClient | None = None,
        repository: WeatherRepository | None = None,
        cache: RedisWeatherCache | None = None,
    ):
        self.client = client or OpenMeteoClient()
        self.repository = repository
        self.cache = cache

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> CanonicalWeather:

        # ---------------------------------------------------------
        # 1. Redis cache lookup
        # ---------------------------------------------------------
        if self.cache is not None:
            try:
                key = self.cache.current_key(
                    latitude,
                    longitude,
                )

                cached = await self.cache.get(key)

                if cached is not None:
                    return CanonicalWeather.model_validate(
                        cached
                    )

            except Exception:
                # Cache failure must not break weather service.
                pass

        # ---------------------------------------------------------
        # 2. Fetch from Open-Meteo
        # ---------------------------------------------------------
        weather = await self.client.get_weather(
            latitude=latitude,
            longitude=longitude,
        )

        # ---------------------------------------------------------
        # 3. Normalize to canonical format
        # ---------------------------------------------------------
        canonical = WeatherNormalizer.normalize(
            weather
        )

        serialized = canonical.model_dump(
            mode="json"
        )

        # ---------------------------------------------------------
        # 4. Persistent MongoDB storage
        # ---------------------------------------------------------
        if self.repository is not None:
            await self.repository.save_current(
                canonical
            )

        # ---------------------------------------------------------
        # 5. Redis cache population
        # ---------------------------------------------------------
        if self.cache is not None:
            try:
                key = self.cache.current_key(
                    latitude,
                    longitude,
                )

                await self.cache.set(
                    key,
                    serialized,
                    ttl=self.cache.CURRENT_TTL,
                )

            except Exception:
                # Cache failure must not break weather service.
                pass

        return canonical

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 7,
    ) -> CanonicalForecast:

        # ---------------------------------------------------------
        # 1. Redis cache lookup
        # ---------------------------------------------------------
        if self.cache is not None:
            try:
                key = self.cache.forecast_key(
                    latitude,
                    longitude,
                )

                cached = await self.cache.get(key)

                if cached is not None:
                    return CanonicalForecast.model_validate(
                        cached
                    )

            except Exception:
                pass

        # ---------------------------------------------------------
        # 2. Fetch forecast
        # ---------------------------------------------------------
        forecast = await self.client.get_forecast(
            latitude=latitude,
            longitude=longitude,
            forecast_days=forecast_days,
        )

        # ---------------------------------------------------------
        # 3. Normalize
        # ---------------------------------------------------------
        canonical = WeatherNormalizer.normalize_forecast(
            forecast
        )

        serialized = canonical.model_dump(
            mode="json"
        )

        # ---------------------------------------------------------
        # 4. MongoDB persistence
        # ---------------------------------------------------------
        if self.repository is not None:
            await self.repository.save_forecast(
                canonical
            )

        # ---------------------------------------------------------
        # 5. Redis cache
        # ---------------------------------------------------------
        if self.cache is not None:
            try:
                key = self.cache.forecast_key(
                    latitude,
                    longitude,
                )

                await self.cache.set(
                    key,
                    serialized,
                    ttl=self.cache.FORECAST_TTL,
                )

            except Exception:
                pass

        return canonical

    async def get_historical(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
    ) -> CanonicalHistorical:

        # ---------------------------------------------------------
        # 1. Redis cache lookup
        # ---------------------------------------------------------
        if self.cache is not None:
            try:
                key = self.cache.historical_key(
                    latitude,
                    longitude,
                    start_date,
                    end_date,
                )

                cached = await self.cache.get(key)

                if cached is not None:
                    return CanonicalHistorical.model_validate(
                        cached
                    )

            except Exception:
                pass

        # ---------------------------------------------------------
        # 2. Fetch historical weather
        # ---------------------------------------------------------
        historical = await self.client.get_historical(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
        )

        # ---------------------------------------------------------
        # 3. Normalize
        # ---------------------------------------------------------
        canonical = WeatherNormalizer.normalize_historical(
            historical
        )

        serialized = canonical.model_dump(
            mode="json"
        )

        # ---------------------------------------------------------
        # 4. MongoDB persistence
        # ---------------------------------------------------------
        if self.repository is not None:
            await self.repository.save_historical(
                canonical
            )

        # ---------------------------------------------------------
        # 5. Redis cache
        # ---------------------------------------------------------
        if self.cache is not None:
            try:
                key = self.cache.historical_key(
                    latitude,
                    longitude,
                    start_date,
                    end_date,
                )

                await self.cache.set(
                    key,
                    serialized,
                    ttl=self.cache.HISTORICAL_TTL,
                )

            except Exception:
                pass

        return canonical

    async def close(self) -> None:
        await self.client.close()