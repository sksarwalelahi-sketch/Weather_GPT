import pytest

from app.workers.ingestion_workers import (
    IngestionFailure,
    IngestionWorkerPool,
)


@pytest.mark.asyncio
async def test_worker_pool_retries_then_succeeds():
    attempts = 0

    async def work():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError("temporary")
        return "ok"

    pool = IngestionWorkerPool(
        worker_count=2,
        max_retries=2,
        retry_base_seconds=0.001,
    )
    try:
        assert await pool.submit("test", work) == "ok"
        assert attempts == 3
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_worker_pool_records_terminal_failure():
    failures: list[IngestionFailure] = []

    async def handle(failure):
        failures.append(failure)

    async def work():
        raise RuntimeError("permanent")

    pool = IngestionWorkerPool(
        max_retries=1,
        retry_base_seconds=0.001,
        failure_handler=handle,
    )
    try:
        with pytest.raises(RuntimeError, match="permanent"):
            await pool.submit("test", work)
    finally:
        await pool.close()

    assert len(failures) == 1
    assert failures[0].operation == "test"
    assert failures[0].attempts == 2
