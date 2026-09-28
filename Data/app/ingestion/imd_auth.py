"""
IMD API Authentication Manager
================================
Handles dual-auth required by api.imd.gov.in:
  - X-API-KEY header  (static, IP-bound key)
  - Authorization: Bearer <JWT> header (expires every 3600 seconds)

JWT is fetched automatically on first use and refreshed before expiry.
Thread-safe via asyncio.Lock.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TOKEN_ENDPOINT = "https://api.imd.gov.in/api/oauth/token.php"
# Refresh 60 seconds before actual expiry to avoid mid-request token failures
_REFRESH_BUFFER_SECONDS = 60


@dataclass
class _TokenCache:
    access_token: str = ""
    expires_at: float = 0.0  # Unix timestamp


class IMDAuthManager:
    """
    Singleton-style JWT + API-Key manager for IMD official APIs.

    Usage
    -----
    auth = IMDAuthManager(api_key="...", email="...", password="...")
    headers = await auth.get_headers()
    response = await client.get(url, headers=headers)
    """

    def __init__(
        self,
        api_key: str,
        email: str,
        password: str,
        token_endpoint: str = _TOKEN_ENDPOINT,
        timeout: float = 15.0,
    ) -> None:
        self.api_key = api_key
        self.email = email
        self.password = password
        self.token_endpoint = token_endpoint
        self.timeout = timeout
        self._cache = _TokenCache()
        self._lock = asyncio.Lock()
        self._http: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_headers(self) -> dict[str, str]:
        """Return auth headers ready to attach to any IMD API request."""
        token = await self._get_valid_token()
        return {
            "X-API-KEY": self.api_key,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def close(self) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_token_valid(self) -> bool:
        return (
            bool(self._cache.access_token)
            and time.monotonic() < self._cache.expires_at - _REFRESH_BUFFER_SECONDS
        )

    async def _get_valid_token(self) -> str:
        if self._is_token_valid():
            return self._cache.access_token

        async with self._lock:
            # Re-check inside lock in case another coroutine just refreshed
            if self._is_token_valid():
                return self._cache.access_token
            await self._refresh_token()
            return self._cache.access_token

    async def _refresh_token(self) -> None:
        client = self._get_http_client()
        payload: dict[str, Any] = {
            "email": self.email,
            "password": self.password,
        }
        try:
            response = await client.post(
                self.token_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            token = data.get("access_token") or data.get("token") or ""
            expires_in = int(data.get("expires_in", 3600))
            if not token:
                raise ValueError(f"No access_token in IMD auth response: {data}")
            self._cache.access_token = token
            self._cache.expires_at = time.monotonic() + expires_in
            logger.info(
                "IMD JWT refreshed successfully; expires in %ds", expires_in
            )
        except httpx.HTTPStatusError as exc:
            logger.error(
                "IMD token refresh failed (HTTP %s): %s",
                exc.response.status_code,
                exc.response.text[:300],
            )
            raise
        except Exception as exc:
            logger.error("IMD token refresh error: %s", exc)
            raise

    def _get_http_client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(timeout=self.timeout)
        return self._http

