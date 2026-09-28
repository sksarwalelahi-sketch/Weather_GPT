"""
Official IMD API Client — api.imd.gov.in
=========================================
Uses Dev Key 1 endpoints (/api/v1):
  - aws_data      : 1,160+ Automated Weather Stations with exact lat/lon
  - current_wx   : 440+ Synoptic current weather observations
  - stationnowcast: Station-wise 0-3hr nowcasts
  - districtnowcast: District-wise nowcasts

Authentication:
  X-API-KEY: <Dev Key 1>
  Authorization: Bearer <JWT> (auto-refreshed via IMDAuthManager)
"""
from __future__ import annotations

import logging
import math
import time
from typing import Any

import httpx

from app.core.config import settings
from app.ingestion.imd_auth import IMDAuthManager
from app.normalization.imd_normalizer import IMDWeatherNormalizer

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


class IMDOfficialClient:
    """
    Client for IMD official API portal (api.imd.gov.in/api/v1).
    Uses Dev Key 1 for observations and nowcasts.
    """

    SOURCE = "imd-official"

    def __init__(
        self,
        auth: IMDAuthManager | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (base_url or settings.IMD_API_BASE).rstrip("/")
        self.timeout = timeout
        self._auth = auth or _make_dev1_auth()
        self._http = httpx.AsyncClient(timeout=timeout)
        self._aws_cache: tuple[float, list[dict[str, Any]]] | None = None

    # ------------------------------------------------------------------
    # Current Weather via AWS (Nearest Automated Weather Station)
    # ------------------------------------------------------------------

    async def _get_all_aws(self) -> list[dict[str, Any]]:
        now = time.monotonic()
        if self._aws_cache is not None:
            cache_time, data = self._aws_cache
            if now - cache_time < 300:  # 5 min cache
                return data

        headers = await self._auth.get_headers()
        url = f"{self.base_url}/{settings.IMD_ENDPOINT_AWS}"
        response = await self._http.get(url, headers=headers)
        response.raise_for_status()
        raw = response.json()
        stations = raw if isinstance(raw, list) else raw.get("data", [])
        self._aws_cache = (now, stations)
        return stations

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        """
        Find the nearest IMD AWS station to the given coordinates and return
        its live observation.
        """
        stations = await self._get_all_aws()
        if not stations:
            raise RuntimeError("No AWS station data returned from IMD API")

        valid_stations = []
        for s in stations:
            try:
                slat = float(s["Latitude"])
                slon = float(s["Longitude"])
                valid_stations.append((s, slat, slon))
            except (KeyError, ValueError, TypeError):
                continue

        if not valid_stations:
            raise RuntimeError("No IMD stations with valid coordinates found")

        nearest, slat, slon = min(
            valid_stations,
            key=lambda item: _haversine_km(latitude, longitude, item[1], item[2]),
        )
        dist_km = _haversine_km(latitude, longitude, slat, slon)

        # Parse observation fields
        temp = None
        for k in ("CURR_TEMP", "Temperature", "temp"):
            val = nearest.get(k)
            if val is not None and val != "":
                try:
                    temp = float(val)
                    break
                except ValueError:
                    pass

        rh = None
        for k in ("RH", "Humidity", "relative_humidity"):
            val = nearest.get(k)
            if val is not None and val != "":
                try:
                    rh = float(val)
                    break
                except ValueError:
                    pass

        feel_like = temp
        fl_val = nearest.get("Feel Like")
        if fl_val is not None and fl_val != "":
            try:
                feel_like = float(fl_val)
            except ValueError:
                pass

        pressure = 1013.25
        for k in ("MSLP", "Mean Sea Level Pressure", "surface_pressure"):
            val = nearest.get(k)
            if val is not None and val != "":
                try:
                    pressure = float(val)
                    break
                except ValueError:
                    pass

        wind_spd = 0.0
        for k in ("WIND_SPEED", "Wind Speed KMPH", "wind_speed"):
            val = nearest.get(k)
            if val is not None and val != "":
                try:
                    wind_spd = float(val)
                    break
                except ValueError:
                    pass

        wind_dir = 0.0
        for k in ("WIND_DIRECTION", "Wind Direction", "wind_direction"):
            val = nearest.get(k)
            if val is not None and val != "":
                try:
                    wind_dir = float(val)
                    break
                except ValueError:
                    pass

        rain = 0.0
        for k in ("RAINFALL", "Last 24 hrs Rainfall", "precipitation"):
            val = nearest.get(k)
            if val is not None and val != "" and val != "NULL":
                try:
                    rain = float(val)
                    break
                except ValueError:
                    pass

        code = 0
        wcode_val = nearest.get("WEATHER_CODE")
        if wcode_val is not None:
            try:
                code = int(wcode_val)
            except ValueError:
                code = 0 if rain == 0 else 61

        desc = nearest.get("WEATHER_MESSAGE") or ("Rain" if rain > 0 else "Clear")

        return {
            "source": self.SOURCE,
            "endpoint": "aws_data",
            "latitude": slat,
            "longitude": slon,
            "distance_km": round(dist_km, 1),
            "data": {
                "station_id": str(nearest.get("ID") or nearest.get("STATION") or ""),
                "station_name": str(nearest.get("STATION") or ""),
                "district": str(nearest.get("DISTRICT") or ""),
                "state": str(nearest.get("STATE") or ""),
                "temperature": temp,
                "apparent_temperature": feel_like,
                "relative_humidity": rh,
                "surface_pressure": pressure,
                "wind_speed": wind_spd,
                "wind_direction": wind_dir,
                "precipitation": rain,
                "weather_code": code,
                "weather_description": desc,
                "observed_at": nearest.get("DATE"),
            },
        }

    # ------------------------------------------------------------------
    # Station-wise Nowcast (stationnowcast)
    # ------------------------------------------------------------------

    async def get_station_nowcast(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        headers = await self._auth.get_headers()
        url = f"{self.base_url}/{settings.IMD_ENDPOINT_STATION_NOWCAST}"
        response = await self._http.get(url, headers=headers)
        response.raise_for_status()
        return {
            "source": self.SOURCE,
            "endpoint": "stationnowcast",
            "latitude": latitude,
            "longitude": longitude,
            "data": response.json(),
        }

    # ------------------------------------------------------------------
    # District-wise Nowcast (districtnowcast)
    # ------------------------------------------------------------------

    async def get_district_nowcast(
        self,
        state: str,
        district: str | None = None,
    ) -> dict[str, Any]:
        headers = await self._auth.get_headers()
        url = f"{self.base_url}/{settings.IMD_ENDPOINT_DISTRICT_NOWCAST}"
        params: dict[str, str] = {"state": state}
        if district:
            params["district"] = district
        response = await self._http.get(url, params=params, headers=headers)
        response.raise_for_status()
        return {
            "source": self.SOURCE,
            "endpoint": "districtnowcast",
            "state": state,
            "district": district,
            "data": response.json(),
        }

    async def close(self) -> None:
        await self._http.aclose()
        await self._auth.close()


class IMDClient:
    """Drop-in replacement for legacy IMDClient."""

    SOURCE = "imd"

    def __init__(self, base_url: str | None = None, timeout: float = 30.0) -> None:
        self._official = IMDOfficialClient(timeout=timeout)

    async def get_weather(self, latitude: float, longitude: float) -> dict[str, Any]:
        return await self._official.get_current_weather(latitude, longitude)

    async def close(self) -> None:
        await self._official.close()


class IMDIngestion:
    """IMD ingestion + normalization + optional persistence."""

    SOURCE = "imd"
    CACHE_TTL = 300

    def __init__(
        self,
        client: IMDClient | None = None,
        repository: Any | None = None,
        cache: Any | None = None,
    ) -> None:
        self.client = client or IMDClient()
        self.repository = repository
        self.cache = cache

    async def ingest_weather(self, latitude: float, longitude: float):
        payload = await self.client.get_weather(latitude, longitude)
        observation = payload.get("data", payload)
        if isinstance(observation, dict):
            observation = dict(observation)
            observation.setdefault("latitude", latitude)
            observation.setdefault("longitude", longitude)

        normalized = IMDWeatherNormalizer.normalize(observation)

        if self.repository is not None:
            await self.repository.save_imd_weather(normalized)

        if self.cache is not None:
            cache_key = f"weather:imd:{normalized.latitude:.6f}:{normalized.longitude:.6f}"
            await self.cache.set(cache_key, normalized.model_dump(mode="json"), ttl=self.CACHE_TTL)

        return normalized

    async def close(self) -> None:
        await self.client.close()


def _make_dev1_auth() -> IMDAuthManager:
    return IMDAuthManager(
        api_key=settings.IMD_DEV_KEY_1,
        email=settings.IMD_EMAIL,
        password=settings.IMD_PASSWORD,
    )


def _make_dev2_auth() -> IMDAuthManager:
    return IMDAuthManager(
        api_key=settings.IMD_DEV_KEY_2,
        email=settings.IMD_EMAIL,
        password=settings.IMD_PASSWORD,
    )
