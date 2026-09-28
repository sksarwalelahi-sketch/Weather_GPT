from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Awaitable, Callable

from app.core.config import settings
from app.core.observability import metrics

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestionFailure:
    operation: str
    error: str
    attempts: int
    failed_at: datetime


class IngestionWorkerPool:
    """Bounded async workers with retry/backoff and failure reporting."""

    def __init__(
        self,
        worker_count: int = settings.INGESTION_WORKER_COUNT,
        max_retries: int = settings.INGESTION_MAX_RETRIES,
        retry_base_seconds: float = settings.INGESTION_RETRY_BASE_SECONDS,
        failure_handler: Callable[
            [IngestionFailure], Awaitable[None]
        ] | None = None,
    ) -> None:
        if worker_count < 1:
            raise ValueError("worker_count must be at least 1")
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if retry_base_seconds <= 0:
            raise ValueError("retry_base_seconds must be positive")

        self.worker_count = worker_count
        self.max_retries = max_retries
        self.retry_base_seconds = retry_base_seconds
        self.failure_handler = failure_handler
        self._queue: asyncio.Queue[
            tuple[str, Callable[[], Awaitable[Any]], asyncio.Future[Any]]
        ] = asyncio.Queue()
        self._workers: list[asyncio.Task[None]] = []
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._workers = [
            asyncio.create_task(
                self._worker_loop(),
                name=f"ingestion-worker-{index}",
            )
            for index in range(self.worker_count)
        ]

    async def submit(
        self,
        operation: str,
        work: Callable[[], Awaitable[Any]],
    ) -> Any:
        if not self._started:
            await self.start()

        future = asyncio.get_running_loop().create_future()
        await self._queue.put((operation, work, future))
        return await future

    async def _worker_loop(self) -> None:
        while True:
            operation, work, future = await self._queue.get()
            try:
                result = await self._run_with_retries(operation, work)
                if not future.done():
                    future.set_result(result)
            except Exception as exc:
                if not future.done():
                    future.set_exception(exc)
            finally:
                self._queue.task_done()

    async def _run_with_retries(
        self,
        operation: str,
        work: Callable[[], Awaitable[Any]],
    ) -> Any:
        attempts = 0
        while True:
            attempts += 1
            try:
                metrics.increment("ingestion_attempts")
                result = await work()
                metrics.increment("ingestion_successes")
                return result
            except Exception as exc:
                if attempts > self.max_retries:
                    metrics.increment("ingestion_failures")
                    failure = IngestionFailure(
                        operation=operation,
                        error=str(exc),
                        attempts=attempts,
                        failed_at=datetime.now(UTC),
                    )
                    if self.failure_handler is not None:
                        await self.failure_handler(failure)
                    logger.error(
                        "ingestion failed permanently",
                        extra={
                            "event": "ingestion_failure",
                            "fields": {
                                "operation": operation,
                                "attempts": attempts,
                                "error": str(exc),
                            },
                        },
                    )
                    raise

                await asyncio.sleep(
                    self.retry_base_seconds * (2 ** (attempts - 1))
                )
                metrics.increment("ingestion_retries")

    async def close(self) -> None:
        if not self._started:
            return

        await self._queue.join()
        for worker in self._workers:
            worker.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        self._started = False
