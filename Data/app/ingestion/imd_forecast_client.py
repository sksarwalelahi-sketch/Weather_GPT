"""
IMD Forecast & Warning Client — api.imd.gov.in
===============================================
Covers Dev Key 2 endpoints (/api/v1):
  - cityforecastloc      : 1,250+ 7-day city forecasts across India
  - cityforecastwarning  : 7-day forecasts bundled with warnings
  - subdivisionwarning   : Color-coded warnings across all 36 Indian subdivisions
  - districtwarning      : District-wise weather warnings (750+ districts)
  - districtrainfall     : District-wise rainfall actual vs normal
  - touristforecast      : Tourist location forecasts
  - sunmoon              : Sunrise/Sunset/Moonrise times
"""
from __future__ import annotations

import logging
import math
import time
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx

from app.core.config import settings
from app.ingestion.imd_auth import IMDAuthManager
from app.models.alert import AlertCreate
from app.normalization.weather_normalizer import CanonicalDailyForecast, CanonicalForecast
from app.services.source_fusion import single_source_score

logger = logging.getLogger(__name__)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def map_imd_weather_code(text: str) -> int:
    t = (text or "").lower()
    if "thunder" in t or "storm" in t or "lightning" in t:
        return 95
    if "heavy rain" in t or "very heavy" in t or "extremely heavy" in t:
        return 65
    if "rain" in t or "shower" in t or "drizzle" in t:
        return 61
    if "fog" in t or "mist" in t:
        return 45
    if "partly cloudy" in t:
        return 2
    if "cloud" in t or "overcast" in t:
        return 3
    if "clear" in t or "sun" in t:
        return 0
    return 3


class IMDForecastClient:
    """
    IMD official forecast & warning API client (Dev Key 2).
    """

    SOURCE = "imd-official-forecast"

    def __init__(
        self,
        auth: IMDAuthManager | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (base_url or settings.IMD_API_BASE).rstrip("/")
        self.timeout = timeout
        self._auth = auth or _make_dev2_auth()
        self._http = httpx.AsyncClient(timeout=timeout)
        self._forecast_cache: tuple[float, list[dict[str, Any]]] | None = None

    # ------------------------------------------------------------------
    # 7-Day City Forecast (Nearest Station Selection)
    # ------------------------------------------------------------------

    async def _get_all_forecasts(self) -> list[dict[str, Any]]:
        now = time.monotonic()
        if self._forecast_cache is not None:
            cache_time, data = self._forecast_cache
            if now - cache_time < 900:  # 15 min cache
                return data

        headers = await self._auth.get_headers()
        url = f"{self.base_url}/{settings.IMD_ENDPOINT_CITY_FORECAST}"
        response = await self._http.get(url, headers=headers)
        response.raise_for_status()
        raw = response.json()
        items = raw if isinstance(raw, list) else raw.get("data", [])
        self._forecast_cache = (now, items)
        return items

    async def get_city_forecast(
        self,
        latitude: float,
        longitude: float,
    ) -> CanonicalForecast:
        """
        Find nearest IMD station from cityforecastloc and build a CanonicalForecast.
        """
        stations = await self._get_all_forecasts()
        if not stations:
            raise RuntimeError("No forecast stations returned from IMD API")

        valid = []
        for s in stations:
            try:
                slat = float(s["Latitude"])
                slon = float(s["Longitude"])
                valid.append((s, slat, slon))
            except (KeyError, ValueError, TypeError):
                continue

        if not valid:
            raise RuntimeError("No IMD forecast stations with coordinates found")

        nearest, slat, slon = min(
            valid,
            key=lambda item: _haversine_km(latitude, longitude, item[1], item[2]),
        )
        dist_km = _haversine_km(latitude, longitude, slat, slon)
        station_name = str(nearest.get("Station_Name") or "IMD Station")

        base_date_str = str(nearest.get("Date") or "")
        try:
            start_date = datetime.strptime(base_date_str, "%Y-%m-%d").date()
        except ValueError:
            start_date = date.today()

        days_spec = [
            (
                start_date,
                nearest.get("Todays_Forecast_Max_Temp") or nearest.get("Today_Max_temp"),
                nearest.get("Todays_Forecast_Min_temp") or nearest.get("Today_Min_temp"),
                nearest.get("Todays_Forecast"),
            ),
            (
                start_date + timedelta(days=1),
                nearest.get("Day_2_Max_Temp"),
                nearest.get("Day_2_Min_temp"),
                nearest.get("Day_2_Forecast"),
            ),
            (
                start_date + timedelta(days=2),
                nearest.get("Day_3_Max_Temp"),
                nearest.get("Day_3_Min_temp"),
                nearest.get("Day_3_Forecast"),
            ),
            (
                start_date + timedelta(days=3),
                nearest.get("Day_4_Max_Temp"),
                nearest.get("Day_4_Min_temp"),
                nearest.get("Day_4_Forecast"),
            ),
            (
                start_date + timedelta(days=4),
                nearest.get("Day_5_Max_Temp"),
                nearest.get("Day_5_Min_temp"),
                nearest.get("Day_5_Forecast"),
            ),
            (
                start_date + timedelta(days=5),
                nearest.get("Day_6_Max_Temp"),
                nearest.get("Day_6_Min_temp"),
                nearest.get("Day_6_Forecast"),
            ),
            (
                start_date + timedelta(days=6),
                nearest.get("Day_7_Max_Temp"),
                nearest.get("Day_7_Min_temp"),
                nearest.get("Day_7_Forecast"),
            ),
        ]

        daily_forecasts: list[CanonicalDailyForecast] = []
        for day_date, max_t, min_t, fcast_text in days_spec:
            try:
                t_max = float(max_t) if max_t is not None else 32.0
            except ValueError:
                t_max = 32.0

            try:
                t_min = float(min_t) if min_t is not None else 24.0
            except ValueError:
                t_min = 24.0

            w_code = map_imd_weather_code(str(fcast_text or ""))
            is_rain = w_code in (61, 65, 95)
            precip = 10.0 if w_code == 65 else (5.0 if is_rain else 0.0)

            daily_forecasts.append(
                CanonicalDailyForecast(
                    date=day_date,
                    temperature_max=t_max,
                    temperature_min=t_min,
                    precipitation=precip,
                    precipitation_probability=80 if w_code == 65 else (60 if is_rain else 10),
                    rain=precip,
                    weather_code=w_code,
                    wind_speed_max=20.0 if w_code in (65, 95) else 12.0,
                    humidity=85.0 if is_rain else 65.0,
                )
            )

        sunrise_val = nearest.get("Sunrise_time")
        sunset_val = nearest.get("Sunset_time")

        return CanonicalForecast(
            latitude=slat,
            longitude=slon,
            timezone="Asia/Kolkata",
            source="imd",
            forecast=daily_forecasts,
            hourly=None,
            sunrise=[str(sunrise_val)] if sunrise_val else None,
            sunset=[str(sunset_val)] if sunset_val else None,
            retrieved_at=datetime.now(UTC),
            provenance={
                "provider": "India Meteorological Department",
                "role": "official 7-day city forecast (cityforecastloc)",
                "status": "live",
                "fusion": "official-source",
                "station_name": station_name,
                "station_code": str(nearest.get("Station_Code") or ""),
                "distance_km": round(dist_km, 1),
                "sources": ["imd-cityforecastloc"],
                **single_source_score("imd-official", datetime.now(UTC)),
            },
        )

    # ------------------------------------------------------------------
    # Subdivision Warnings (Color-coded warnings across India)
    # ------------------------------------------------------------------

    async def get_subdivision_warnings(self) -> list[dict[str, Any]]:
        headers = await self._auth.get_headers()
        url = f"{self.base_url}/subdivisionwarning"
        response = await self._http.get(url, headers=headers)
        response.raise_for_status()
        raw = response.json()
        return raw if isinstance(raw, list) else raw.get("data", [])

    # ------------------------------------------------------------------
    # District-wise Warnings
    # ------------------------------------------------------------------

    async def get_district_warnings(self) -> list[dict[str, Any]]:
        headers = await self._auth.get_headers()
        url = f"{self.base_url}/{settings.IMD_ENDPOINT_DISTRICT_WARNING}"
        response = await self._http.get(url, headers=headers)
        response.raise_for_status()
        raw = response.json()
        return raw if isinstance(raw, list) else raw.get("data", [])

    async def close(self) -> None:
        await self._http.aclose()
        await self._auth.close()


def _make_dev2_auth() -> IMDAuthManager:
    return IMDAuthManager(
        api_key=settings.IMD_DEV_KEY_2,
        email=settings.IMD_EMAIL,
        password=settings.IMD_PASSWORD,
    )
