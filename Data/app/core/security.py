from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.observability import metrics


logger = logging.getLogger("weathergpt.api")


class APIProtectionMiddleware(BaseHTTPMiddleware):
    """Apply optional API-key authentication and per-process rate limiting."""

    EXEMPT_PATHS = {
        "/",
        "/health",
        "/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable],
    ):
        started = time.perf_counter()
        path = request.url.path

        if request.method != "OPTIONS" and path not in self.EXEMPT_PATHS:
            configured_keys = settings.API_KEYS
            if configured_keys:
                supplied_key = request.headers.get("X-API-Key")
                if supplied_key not in configured_keys:
                    response = JSONResponse(
                        {"detail": "Invalid or missing API key"},
                        status_code=401,
                    )
                    logger.info(
                        "request rejected",
                        extra={
                            "event": "http_request",
                            "fields": {
                                "method": request.method,
                                "path": path,
                                "status_code": response.status_code,
                                "duration_ms": round(
                                    (time.perf_counter() - started) * 1000,
                                    3,
                                ),
                            },
                        },
                    )
                    return response

            client = request.client.host if request.client else "unknown"
            identity = request.headers.get("X-API-Key") or client
            now = time.monotonic()
            window_start = now - 60
            timestamps = self._requests[identity]
            while timestamps and timestamps[0] <= window_start:
                timestamps.popleft()
            if len(timestamps) >= settings.RATE_LIMIT_PER_MINUTE:
                response = JSONResponse(
                    {"detail": "Rate limit exceeded"},
                    status_code=429,
                    headers={"Retry-After": "60"},
                )
                logger.info(
                    "request rejected",
                    extra={
                        "event": "http_request",
                        "fields": {
                            "method": request.method,
                            "path": path,
                            "status_code": response.status_code,
                            "duration_ms": round(
                                (time.perf_counter() - started) * 1000,
                                3,
                            ),
                        },
                    },
                )
                return response
            timestamps.append(now)

        response = await call_next(request)
        metrics.increment("http_requests")
        logger.info(
            "request completed",
            extra={
                "event": "http_request",
                "fields": {
                    "method": request.method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": round(
                        (time.perf_counter() - started) * 1000,
                        3,
                    ),
                },
            },
        )
        return response
