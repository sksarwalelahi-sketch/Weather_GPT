import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.weather import router as weather_router
from app.api.websockets import router as websocket_router
from app.api.alerts import router as alerts_router
from app.core.config import get_scheduler_locations, settings
from app.database.mongodb import mongodb
from app.core.dependencies import alert_repository, weather_repository
from app.scheduler.weather_scheduler import WeatherScheduler
from app.gfs.ingestion import GFSIngestion
from app.core.dependencies import redis_cache
from app.workers.ingestion_workers import (
    IngestionFailure,
    IngestionWorkerPool,
)
from app.core.security import APIProtectionMiddleware
from app.core.observability import configure_logging, metrics
from app.api.websockets import live_updates
from app.ingestion.official_alerts import OfficialIMDWarningClient, normalize_wis2_notification
from app.ingestion.wis2_ingestion import WIS2WeatherIngestion


logger = logging.getLogger(__name__)


configure_logging()


async def record_ingestion_failure(
    failure: IngestionFailure,
) -> None:
    await weather_repository.save_failed_ingestion(failure)
    await live_updates.publish(
        "alerts",
        {
            "type": "ingestion_failure",
            "operation": failure.operation,
            "error": failure.error,
            "attempts": failure.attempts,
            "failed_at": failure.failed_at.isoformat(),
        },
    )


scheduler = WeatherScheduler(
    redis_cache=redis_cache,
    gfs_ingestion=GFSIngestion(
        repository=weather_repository,
    ),
    interval_minutes=15,
    worker_pool=IngestionWorkerPool(
        failure_handler=record_ingestion_failure,
    ),
)


async def _persist_official_alerts(alerts) -> None:
    for alert in alerts:
        document, created = await alert_repository.upsert_official(alert)
        if created:
            await live_updates.publish("alerts", document)


async def _wis2_warning_loop() -> None:
    consumer = WIS2WeatherIngestion()
    try:
        await consumer.connect()
        while True:
            payload = await consumer.get_message()
            await _persist_official_alerts(normalize_wis2_notification(payload))
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("WIS2 official warning ingestion stopped")
    finally:
        await consumer.disconnect()


async def _imd_warning_loop() -> None:
    # Use Dev Key 2 for cityforecastwarning / districtwarning endpoints.
    # Falls back to the legacy IMD_WARNINGS_API_KEY if Dev Key 2 is not set.
    api_key = settings.IMD_DEV_KEY_2 or settings.IMD_WARNINGS_API_KEY
    client = OfficialIMDWarningClient(
        settings.IMD_WARNINGS_URL,
        api_key,
    )
    try:
        while True:
            await _persist_official_alerts(await client.fetch())
            await asyncio.sleep(settings.IMD_WARNINGS_POLL_MINUTES * 60)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("IMD official warning ingestion stopped")
    finally:
        await client.close()


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Connect shared MongoDB instance
    last_error: Exception | None = None
    for attempt in range(1, settings.MONGODB_STARTUP_RETRIES + 1):
        try:
            await mongodb.connect()
            await alert_repository.ensure_indexes()
            break
        except Exception as exc:
            last_error = exc
            await mongodb.disconnect()
            if attempt == settings.MONGODB_STARTUP_RETRIES:
                raise RuntimeError(
                    "MongoDB startup failed after "
                    f"{attempt} attempts. Verify that the Atlas cluster "
                    "has an elected primary, the current IP is allowed, "
                    "and Data/.env contains a valid MONGODB_URI."
                ) from exc
            logger.warning(
                "MongoDB startup attempt %s/%s failed: %s; retrying in %ss",
                attempt,
                settings.MONGODB_STARTUP_RETRIES,
                exc,
                settings.MONGODB_STARTUP_RETRY_DELAY_SECONDS,
            )
            await asyncio.sleep(
                settings.MONGODB_STARTUP_RETRY_DELAY_SECONDS
            )

    for index, (latitude, longitude) in enumerate(
        get_scheduler_locations(),
        start=1,
    ):
        suffix = f"location-{index}"
        scheduler.add_current_weather_job(
            latitude=latitude,
            longitude=longitude,
            job_id=f"{scheduler.CURRENT_JOB_ID}-{suffix}",
        )
        for forecast_hour in (0, 6, 12, 18, 24):
            scheduler.add_gfs_job(
                latitude=latitude,
                longitude=longitude,
                output_directory=f"data/gfs/{suffix}",
                forecast_hour=forecast_hour,
                job_id=f"{scheduler.GFS_JOB_ID}-{suffix}-f{forecast_hour:03d}",
            )
        scheduler.add_era5_job(
            latitude=latitude,
            longitude=longitude,
            output_directory=f"data/era5/{suffix}",
            job_id=f"{scheduler.ERA5_JOB_ID}-{suffix}",
        )

    scheduler.start()
    warning_tasks: list[asyncio.Task[None]] = []
    if settings.WIS2_WARNINGS_ENABLED:
        warning_tasks.append(asyncio.create_task(_wis2_warning_loop(), name="wis2-warning-ingestion"))
    if settings.IMD_WARNINGS_ENABLED and settings.IMD_WARNINGS_URL:
        warning_tasks.append(asyncio.create_task(_imd_warning_loop(), name="imd-warning-ingestion"))

    yield

    for task in warning_tasks:
        task.cancel()
    await asyncio.gather(*warning_tasks, return_exceptions=True)
    await scheduler.close()

    # Disconnect shared MongoDB instance
    await mongodb.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    description="Weather data and NWP backend for WeatherGPT.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.CORS_ORIGINS),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(APIProtectionMiddleware)

app.include_router(weather_router)
app.include_router(websocket_router)
app.include_router(alerts_router)


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


@app.get("/ready")
async def readiness_check(response: Response):
    """Report whether required persistence and cache dependencies are ready."""
    checks: dict[str, str] = {}
    try:
        checks["mongodb"] = "ready" if await mongodb.ping() else "unavailable"
    except Exception as exc:
        checks["mongodb"] = f"error: {type(exc).__name__}"

    try:
        checks["redis"] = (
            "ready" if await redis_cache.ping() else "unavailable"
        )
    except Exception as exc:
        checks["redis"] = f"error: {type(exc).__name__}"

    ready = all(status == "ready" for status in checks.values())
    if not ready:
        response.status_code = 503
    return {
        "status": "ready" if ready else "not_ready",
        "service": "weather-data-platform",
        "checks": checks,
    }


@app.get("/metrics")
def metrics_snapshot():
    return metrics.snapshot()