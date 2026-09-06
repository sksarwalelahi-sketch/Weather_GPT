from app.cache.redis_cache import RedisWeatherCache
from app.repositories.weather_repository import WeatherRepository


class GFSWeatherService:
    CACHE_TTL = RedisWeatherCache.GFS_TTL

    def __init__(
        self,
        repository: WeatherRepository,
        cache: RedisWeatherCache,
    ):
        self.repository = repository
        self.cache = cache

    @staticmethod
    def cache_key(
        latitude: float,
        longitude: float,
    ) -> str:
        return (
            f"weather:gfs:latest:"
            f"{latitude:.6f}:"
            f"{longitude:.6f}"
        )

    async def get_latest(
        self,
        latitude: float,
        longitude: float,
    ) -> dict | None:

        key = self.cache_key(
            latitude,
            longitude,
        )

        # 1. Try Redis first
        try:
            cached = await self.cache.get(key)

            if cached is not None:
                return cached

        except Exception:
            # Cache failure should not break
            # the weather API.
            pass

        # 2. Read latest GFS data from repository
        data = await self.repository.get_latest_gfs(
            latitude=latitude,
            longitude=longitude,
        )

        if data is None:
            return None

        # 3. Store result in Redis
        try:
            await self.cache.set(
                key,
                data,
                ttl=self.CACHE_TTL,
            )
        except Exception:
            # Cache failure should not break
            # the weather API.
            pass

        return data