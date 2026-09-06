import pytest
import pytest_asyncio

from app.cache.redis_cache import RedisWeatherCache


@pytest_asyncio.fixture
async def cache():
    redis_cache = RedisWeatherCache()

    await redis_cache.clear_weather_cache()

    yield redis_cache

    await redis_cache.clear_weather_cache()
    await redis_cache.close()


@pytest.mark.asyncio
async def test_redis_ping(cache):
    assert await cache.ping() is True


@pytest.mark.asyncio
async def test_cache_set_and_get(cache):
    key = "weather:test"

    value = {
        "temperature": 27.5,
        "humidity": 80,
    }

    result = await cache.set(
        key,
        value,
        ttl=60,
    )

    assert result is True

    cached = await cache.get(key)

    assert cached == value


@pytest.mark.asyncio
async def test_cache_miss(cache):
    result = await cache.get(
        "weather:missing"
    )

    assert result is None


@pytest.mark.asyncio
async def test_cache_exists(cache):
    key = "weather:exists"

    await cache.set(
        key,
        {
            "value": 123,
        },
        ttl=60,
    )

    assert await cache.exists(key) is True


@pytest.mark.asyncio
async def test_cache_delete(cache):
    key = "weather:delete"

    await cache.set(
        key,
        {
            "value": 123,
        },
        ttl=60,
    )

    deleted = await cache.delete(key)

    assert deleted is True
    assert await cache.get(key) is None


def test_current_key():
    key = RedisWeatherCache.current_key(
        latitude=20.2961,
        longitude=85.8245,
    )

    assert key == (
        "weather:current:"
        "20.296100:85.824500"
    )


def test_forecast_key():
    key = RedisWeatherCache.forecast_key(
        latitude=20.2961,
        longitude=85.8245,
    )

    assert key == (
        "weather:forecast:"
        "20.296100:85.824500"
    )


def test_historical_key():
    key = RedisWeatherCache.historical_key(
        latitude=20.2961,
        longitude=85.8245,
        start_date="2026-08-01",
        end_date="2026-08-07",
    )

    assert key == (
        "weather:historical:"
        "20.296100:85.824500:"
        "2026-08-01:"
        "2026-08-07"
    )


def test_gfs_key():
    key = RedisWeatherCache.gfs_key(
        latitude=20.2961,
        longitude=85.8245,
        valid_at="2026-08-30T12:00:00",
    )

    assert key == (
        "weather:gfs:"
        "20.296100:85.824500:"
        "2026-08-30T12:00:00"
    )


def test_invalid_port():
    with pytest.raises(ValueError):
        RedisWeatherCache(port=70000)


def test_invalid_ttl():
    with pytest.raises(ValueError):
        RedisWeatherCache(default_ttl=0)


def test_empty_host():
    with pytest.raises(ValueError):
        RedisWeatherCache(host="")


@pytest.mark.asyncio
async def test_cache_clear(cache):
    await cache.set(
        "weather:test:one",
        {"value": 1},
        ttl=60,
    )

    await cache.set(
        "weather:test:two",
        {"value": 2},
        ttl=60,
    )

    await cache.clear_weather_cache()

    assert (
        await cache.get("weather:test:one")
        is None
    )

    assert (
        await cache.get("weather:test:two")
        is None
    )