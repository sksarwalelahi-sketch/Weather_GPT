from __future__ import annotations

import logging
import os
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


logger = logging.getLogger("weathergpt.intelligence.api")
API_KEYS = frozenset(
    key.strip()
    for key in os.getenv("API_KEYS", "").split(",")
    if key.strip()
)
RATE_LIMIT_PER_MINUTE = int(
    os.getenv("RATE_LIMIT_PER_MINUTE", "120")
)
CORS_ORIGINS = tuple(
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173",
    ).split(",")
    if origin.strip()
)


class APIProtectionMiddleware(BaseHTTPMiddleware):
    EXEMPT_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}

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
            if API_KEYS and request.headers.get("X-API-Key") not in API_KEYS:
                return self._logged_response(
                    request,
                    started,
                    JSONResponse(
                        {"detail": "Invalid or missing API key"},
                        status_code=401,
                    ),
                )

            identity = request.headers.get("X-API-Key") or (
                request.client.host if request.client else "unknown"
            )
            now = time.monotonic()
            timestamps = self._requests[identity]
            while timestamps and timestamps[0] <= now - 60:
                timestamps.popleft()
            if len(timestamps) >= RATE_LIMIT_PER_MINUTE:
                return self._logged_response(
                    request,
                    started,
                    JSONResponse(
                        {"detail": "Rate limit exceeded"},
                        status_code=429,
                        headers={"Retry-After": "60"},
                    ),
                )
            timestamps.append(now)

        response = await call_next(request)
        logger.info(
            "%s %s %s %.3f",
            request.method,
            path,
            response.status_code,
            time.perf_counter() - started,
        )
        return response

    @staticmethod
    def _logged_response(request, started, response):
        logger.info(
            "%s %s %s %.3f",
            request.method,
            request.url.path,
            response.status_code,
            time.perf_counter() - started,
        )
        return response
