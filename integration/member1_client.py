"""
WeatherGPT - Member 3
Member 1 HTTP Client

Provides a small HTTP client for consuming the actual
Member 1 Weather Data & NWP FastAPI endpoints.

Responsibilities:
    HTTP request -> JSON response

This module does NOT:
    - perform weather intelligence
    - calculate risk
    - detect hazards
    - generate advisories
    - transform M1 fields into WeatherInput

Those responsibilities belong to member1_adapter.py
and the intelligence engine.
"""

from __future__ import annotations

import json
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from typing import Any


class Member1APIError(RuntimeError):
    """Raised when the Member 1 API request fails."""


class Member1Client:
    """
    HTTP client for the Member 1 Weather Data & NWP API.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # -----------------------------------------------------------------
    # Internal HTTP helper
    # -----------------------------------------------------------------

    def _get(
        self,
        endpoint: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Perform a GET request and return the decoded JSON object.
        """

        query = urlencode(params)

        url = f"{self.base_url}{endpoint}?{query}"

        request = Request(
            url,
            method="GET",
            headers={
                "Accept": "application/json",
            },
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                body = response.read().decode("utf-8")

        except HTTPError as exc:
            raise Member1APIError(
                f"Member 1 API returned HTTP {exc.code} "
                f"for {endpoint}."
            ) from exc

        except URLError as exc:
            raise Member1APIError(
                f"Unable to connect to Member 1 API at "
                f"{self.base_url}."
            ) from exc

        except TimeoutError as exc:
            raise Member1APIError(
                f"Request to Member 1 API timed out "
                f"after {self.timeout} seconds."
            ) from exc

        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            raise Member1APIError(
                f"Member 1 API returned invalid JSON "
                f"for {endpoint}."
            ) from exc

        if not isinstance(data, dict):
            raise Member1APIError(
                f"Member 1 API returned an unexpected JSON "
                f"structure for {endpoint}."
            )

        return data

    # -----------------------------------------------------------------
    # Current Weather
    # -----------------------------------------------------------------

    def get_current(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        """
        Fetch current weather from Member 1.

        Endpoint:
            GET /weather/current
        """

        return self._get(
            "/weather/current",
            {
                "latitude": latitude,
                "longitude": longitude,
            },
        )

    # -----------------------------------------------------------------
    # Forecast
    # -----------------------------------------------------------------

    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 7,
    ) -> dict[str, Any]:
        """
        Fetch daily weather forecast from Member 1.

        Endpoint:
            GET /weather/forecast
        """

        if not 1 <= forecast_days <= 16:
            raise ValueError(
                "forecast_days must be between 1 and 16."
            )

        return self._get(
            "/weather/forecast",
            {
                "latitude": latitude,
                "longitude": longitude,
                "forecast_days": forecast_days,
            },
        )

    # -----------------------------------------------------------------
    # Historical Weather
    # -----------------------------------------------------------------

    def get_historical(
        self,
        latitude: float,
        longitude: float,
        start_date: date | str,
        end_date: date | str,
    ) -> dict[str, Any]:
        """
        Fetch historical daily weather from Member 1.

        Endpoint:
            GET /weather/historical
        """

        if isinstance(start_date, date):
            start_date = start_date.isoformat()

        if isinstance(end_date, date):
            end_date = end_date.isoformat()

        return self._get(
            "/weather/historical",
            {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date,
                "end_date": end_date,
            },
        )