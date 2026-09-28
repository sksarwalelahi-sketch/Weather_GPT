import json
from datetime import UTC, datetime

import pytest
from fastapi import Response

from app.core.observability import JsonFormatter, Metrics
from app.main import readiness_check, record_ingestion_failure
from app.workers.ingestion_workers import IngestionFailure


def test_json_formatter_includes_event_fields():
    import logging

    record = logging.LogRecord(
        "test",
        logging.INFO,
        __file__,
        1,
        "request completed",
        (),
        None,
    )
    record.event = "http_request"
    record.fields = {"status_code": 200}

    payload = json.loads(JsonFormatter().format(record))

    assert payload["event"] == "http_request"
    assert payload["status_code"] == 200


def test_metrics_snapshot_tracks_counters():
    metrics = Metrics()
    metrics.increment("test_counter", 2)

    snapshot = metrics.snapshot()

    assert snapshot["counters"]["test_counter"] == 2
    assert snapshot["uptime_seconds"] >= 0


@pytest.mark.asyncio
async def test_readiness_reports_dependency_status(monkeypatch):
    from app.main import mongodb, redis_cache

    async def mongo_ready():
        return True

    async def redis_ready():
        return True

    monkeypatch.setattr(mongodb, "ping", mongo_ready)
    monkeypatch.setattr(redis_cache, "ping", redis_ready)
    response = Response()

    result = await readiness_check(response)

    assert response.status_code == 200
    assert result["status"] == "ready"
    assert result["checks"] == {"mongodb": "ready", "redis": "ready"}


@pytest.mark.asyncio
async def test_failure_handler_persists_and_notifies(monkeypatch):
    from app.main import live_updates, weather_repository

    saved = []
    published = []

    async def save(failure):
        saved.append(failure)
        return "failure-id"

    async def publish(channel, payload):
        published.append((channel, payload))

    monkeypatch.setattr(weather_repository, "save_failed_ingestion", save)
    monkeypatch.setattr(live_updates, "publish", publish)
    failure = IngestionFailure(
        operation="weather.current",
        error="upstream unavailable",
        attempts=3,
        failed_at=datetime.now(UTC),
    )

    await record_ingestion_failure(failure)

    assert saved == [failure]
    assert published[0][0] == "alerts"
    assert published[0][1]["type"] == "ingestion_failure"
    assert published[0][1]["operation"] == "weather.current"
