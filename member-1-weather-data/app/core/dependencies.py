from app.cache.redis_cache import RedisWeatherCache
from app.core.config import settings
from app.database.mongodb import mongodb
from app.repositories.weather_repository import MongoWeatherRepository


redis_cache = RedisWeatherCache(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
)

weather_repository = MongoWeatherRepository(
    mongodb
)