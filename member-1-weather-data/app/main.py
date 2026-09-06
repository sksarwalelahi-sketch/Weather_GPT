from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.weather import router as weather_router
from app.core.config import settings
from app.database.mongodb import mongodb
from app.scheduler.weather_scheduler import WeatherScheduler
from app.core.dependencies import redis_cache


scheduler = WeatherScheduler(
    redis_cache=redis_cache,
    interval_minutes=15,
)


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Connect shared MongoDB instance
    await mongodb.connect()

    scheduler.add_current_weather_job(
        latitude=20.2961,
        longitude=85.8245,
    )

    scheduler.add_gfs_job(
    latitude=20.2961,
    longitude=85.8245,
)

    scheduler.add_era5_job(
    latitude=20.2961,
    longitude=85.8245,
)

    scheduler.start()


    yield

    await scheduler.close()

    # Disconnect shared MongoDB instance
    await mongodb.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    description="Weather data and NWP backend for WeatherGPT.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(weather_router)


@app.get("/")
def root():
    return {
        "message": "WeatherGPT Weather Data Platform is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "weather-data-platform"
    }