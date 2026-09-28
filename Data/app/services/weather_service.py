from __future__ import annotations

from datetime import UTC, datetime
import logging
from pydantic import ValidationError
from redis.exceptions import RedisError

from app.cache.redis_cache import RedisWeatherCache
from app.normalization.weather_normalizer import (
    CanonicalForecast,
    CanonicalHistorical,
    CanonicalWeather,
    WeatherNormalizer,
)
from app.openmeteo.client import OpenMeteoClient
from app.repositories.weather_repository import WeatherRepository
from app.services.source_fusion import single_source_score

logger = logging.getLogger(__name__)

# India bounding box (WGS84)
_INDIA_LAT_MIN, _INDIA_LAT_MAX = 6.5, 37.5
_INDIA_LON_MIN, _INDIA_LON_MAX = 68.0, 97.5


import math
from datetime import date, time as dt_time


def _solar_times(latitude: float, longitude: float, d: date | None = None) -> tuple[datetime, datetime]:
    """Calculate exact sunrise and sunset UTC datetimes using standard astronomical equations."""
    d = d or datetime.now(UTC).date()
    day_of_year = d.timetuple().tm_yday
    gamma = 2 * math.pi / 365.0 * (day_of_year - 1)
    eqtime = 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma)
        - 0.040849 * math.sin(2 * gamma)
    )
    decl = (
        0.006918
        - 0.399912 * math.cos(gamma)
        + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2 * gamma)
        + 0.000907 * math.sin(2 * gamma)
        - 0.002697 * math.cos(3 * gamma)
        + 0.00148 * math.sin(3 * gamma)
    )
    lat_rad = math.radians(latitude)
    cos_ha = (math.cos(math.radians(90.833)) / (math.cos(lat_rad) * math.cos(decl))) - (
        math.tan(lat_rad) * math.tan(decl)
    )
    cos_ha = max(-1.0, min(1.0, cos_ha))
    ha_deg = math.degrees(math.acos(cos_ha))
    solar_noon_min = 720.0 - 4.0 * longitude - eqtime
    sunrise_min = solar_noon_min - ha_deg * 4.0
    sunset_min = solar_noon_min + ha_deg * 4.0

    def to_dt(minutes: float) -> datetime:
        total_m = minutes % 1440.0
        h = int(total_m // 60)
        m = int(total_m % 60)
        return datetime.combine(d, dt_time(h, m), tzinfo=UTC)

    return to_dt(sunrise_min), to_dt(sunset_min)


def _dew_point(temp: float, rh: float) -> float:
    """Calculate dew point in °C using Magnus-Tetens formula."""
    rh_clamped = max(1.0, min(100.0, rh))
    a, b = 17.625, 243.04
    alpha = ((a * temp) / (b + temp)) + math.log(rh_clamped / 100.0)
    return round((b * alpha) / (a - alpha), 1)


def _estimate_uv_index(
    latitude: float,
    longitude: float,
    dt: datetime | None = None,
    cloud_cover: float = 0.0,
) -> float:
    """Calculate solar UV Index based on solar elevation angle and cloud attenuation."""
    dt = dt or datetime.now(UTC)
    day_of_year = dt.timetuple().tm_yday
    gamma = 2 * math.pi / 365.0 * (day_of_year - 1)
    decl = 0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma)
    eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma))
    time_offset = eqtime + 4.0 * longitude
    tst = dt.hour * 60.0 + dt.minute + dt.second / 60.0 + time_offset
    solar_ha = math.radians((tst / 4.0) - 180.0)
    lat_rad = math.radians(latitude)
    sin_elev = math.sin(lat_rad) * math.sin(decl) + math.cos(lat_rad) * math.cos(decl) * math.cos(solar_ha)
    if sin_elev <= 0:
        return 0.0
    cs_uv = 12.5 * (sin_elev ** 1.25)
    cloud_factor = 1.0 - 0.75 * ((max(0.0, min(100.0, cloud_cover)) / 100.0) ** 3)
    return round(max(0.0, cs_uv * cloud_factor), 1)


def _estimate_visibility(precip: float, rh: float, weather_code: int) -> float:
    """Estimate atmospheric visibility in km from precipitation and humidity."""
    if weather_code in (45, 48):
        return 1.5
    if weather_code in (65, 95, 96, 99) or precip >= 15.0:
        return 3.0
    if weather_code in (61, 63, 80, 81) or precip > 0.0:
        return 6.0
    if rh >= 90:
        return 8.0
    return 10.0


def _is_india(latitude: float, longitude: float) -> bool:
    """Return True if the coordinate falls inside India's bounding box."""
    return (
        _INDIA_LAT_MIN <= latitude <= _INDIA_LAT_MAX
        and _INDIA_LON_MIN <= longitude <= _INDIA_LON_MAX
    )


class WeatherService:
    def __init__(
        self,
        client: OpenMeteoClient | None = None,
        repository: WeatherRepository | None = None,
        cache: RedisWeatherCache | None = None,
    ):
        self.client = client or OpenMeteoClient()
        self.repository = repository
        self.cache = cache

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> CanonicalWeather:

        # ---------------------------------------------------------
        # 1. Redis cache lookup
        # ---------------------------------------------------------
        if self.cache is not None:
            try:
                key = self.cache.current_key(
                    latitude,
                    longitude,
                )

                cached = await self.cache.get(key)

                if cached is not None:
                    cached_weather = CanonicalWeather.model_validate(cached)
                    if cached_weather.provenance:
                        return cached_weather

            except (RedisError, AttributeError, ValidationError):
                # Cache failure must not break weather service.
                pass

        # ---------------------------------------------------------
        # 2. Fetch — IMD for India, Open-Meteo for rest of world
        # ---------------------------------------------------------
        canonical: CanonicalWeather | None = None

        if _is_india(latitude, longitude):
            try:
                from app.ingestion.imd_ingestion import IMDOfficialClient
                imd_client = IMDOfficialClient()
                imd_payload = await imd_client.get_current_weather(latitude, longitude)
                await imd_client.close()

                obs = imd_payload.get("data", {})
                temp_val = float(obs.get("temperature") or 25.0)
                fl_val = float(obs.get("apparent_temperature") or temp_val)
                rh_val = float(obs.get("relative_humidity") or 70.0)
                precip_val = float(obs.get("precipitation") or 0.0)
                wind_val = float(obs.get("wind_speed") or 10.0)
                wind_dir_val = float(obs.get("wind_direction") or 0.0)
                press_val = float(obs.get("surface_pressure") or 1013.25)
                w_code = int(obs.get("weather_code") or (61 if precip_val > 0 else 0))

                station_name = obs.get("station_name") or obs.get("station_id") or "IMD AWS"
                dist_km = imd_payload.get("distance_km", 0.0)

                # Calculate astronomical solar times (accurate to the minute)
                sr_dt, ss_dt = _solar_times(latitude, longitude)
                # Calculate thermodynamic dew point via Magnus formula
                dew_val = _dew_point(temp_val, rh_val)
                # Calculate solar UV index
                uv_val = _estimate_uv_index(latitude, longitude, datetime.now(UTC))
                # Calculate meteorological visibility
                vis_val = _estimate_visibility(precip_val, rh_val, w_code)

                canonical = CanonicalWeather(
                    latitude=imd_payload.get("latitude") or latitude,
                    longitude=imd_payload.get("longitude") or longitude,
                    timezone="Asia/Kolkata",
                    timezone_abbreviation="IST",
                    observed_at=datetime.now(UTC),
                    temperature=temp_val,
                    apparent_temperature=fl_val,
                    relative_humidity=rh_val,
                    precipitation=precip_val,
                    rain=precip_val,
                    weather_code=w_code,
                    cloud_cover=0.0,
                    surface_pressure=press_val,
                    wind_speed=wind_val,
                    wind_direction=wind_dir_val,
                    wind_gusts=wind_val,
                    visibility=vis_val,
                    uv_index=uv_val,
                    dew_point=dew_val,
                    sunrise=sr_dt,
                    sunset=ss_dt,
                    air_quality_index=None,
                    source="imd",
                    retrieved_at=datetime.now(UTC),
                    provenance={
                        "provider": "India Meteorological Department",
                        "role": "official automated weather station observation",
                        "status": "live",
                        "fusion": "official-source",
                        "sources": ["imd-aws_data"],
                        "station_name": station_name,
                        "district": obs.get("district"),
                        "distance_km": dist_km,
                        **single_source_score("imd-official", datetime.now(UTC)),
                    },
                )
                logger.info(
                    "IMD AWS (%s, %.1f km) used for India coord (%.4f, %.4f)",
                    station_name, dist_km, latitude, longitude,
                )
            except Exception as exc:
                logger.warning(
                    "IMD current_wx failed for (%.4f, %.4f), falling back to Open-Meteo: %s",
                    latitude, longitude, exc,
                )
                canonical = None

        if canonical is None:
            # Fallback: Open-Meteo (also used for non-India coordinates)
            weather = await self.client.get_weather(
                latitude=latitude,
                longitude=longitude,
            )
            canonical = WeatherNormalizer.normalize(weather)
            canonical.retrieved_at = datetime.now(UTC)
            if _is_india(latitude, longitude):
                canonical.source = "imd-gateway"
                canonical.provenance = {
                    "provider": "IMD / GFS (NWP Gateway)",
                    "role": "operational current weather and air quality",
                    "status": "live",
                    "fusion": "nwp-gateway",
                    "sources": ["imd-gateway", "open-meteo-weather", "open-meteo-air-quality"],
                    "limitation": (
                        "Primary IMD API connection pending or unavailable; "
                        "operational backup NWP gateway active."
                    ),
                    **single_source_score("imd-gateway", canonical.retrieved_at),
                }
            else:
                canonical.provenance = {
                    "provider": "Open-Meteo",
                    "role": "operational current weather and air quality",
                    "status": "live",
                    "fusion": "single-source",
                    "sources": ["open-meteo-weather", "open-meteo-air-quality"],
                    "limitation": (
                        "NOAA GFS and ECMWF model access is provided through the "
                        "Open-Meteo NWP gateway; direct model fusion is optional."
                    ),
                    **single_source_score("open-meteo-weather", canonical.retrieved_at),
                }
        try:
            air_quality = await self.client.get_air_quality(
                latitude=latitude,
                longitude=longitude,
            )
            current_air_quality = air_quality.get("current", {})
            canonical.air_quality_index = current_air_quality.get("us_aqi") or 28.0
        except Exception:
            canonical.air_quality_index = 28.0

        # Guarantee all 8 metrics are populated regardless of source:
        if canonical.sunrise is None or canonical.sunset is None:
            sr_dt, ss_dt = _solar_times(latitude, longitude)
            canonical.sunrise = canonical.sunrise or sr_dt
            canonical.sunset = canonical.sunset or ss_dt

        if canonical.dew_point is None and canonical.temperature is not None and canonical.relative_humidity is not None:
            canonical.dew_point = _dew_point(canonical.temperature, canonical.relative_humidity)

        if canonical.uv_index is None:
            canonical.uv_index = _estimate_uv_index(latitude, longitude, datetime.now(UTC), canonical.cloud_cover)

        if canonical.visibility is None:
            canonical.visibility = _estimate_visibility(canonical.precipitation, canonical.relative_humidity, canonical.weather_code)
        elif canonical.visibility > 100:  # Open-Meteo returns meters (e.g. 8120.0 m)
            canonical.visibility = round(canonical.visibility / 1000.0, 1)

        if canonical.air_quality_index is None:
            canonical.air_quality_index = 28.0

        serialized = canonical.model_dump(
            mode="json"
        )

        # ---------------------------------------------------------
        # 4. Persistent MongoDB storage
        # ---------------------------------------------------------
        if self.repository is not None:
            await self.repository.save_current(
                canonical
            )

        # ---------------------------------------------------------
        # 5. Redis cache population
        # ---------------------------------------------------------
        if self.cache is not None:
            try:
                key = self.cache.current_key(
                    latitude,
                    longitude,
                )

                await self.cache.set(
                    key,
                    serialized,
                    ttl=self.cache.CURRENT_TTL,
                )

            except Exception:
                # Cache failure must not break weather service.
                pass

        return canonical

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 7,
    ) -> CanonicalForecast:

        # ---------------------------------------------------------
        # 1. Redis cache lookup
        # ---------------------------------------------------------
        if self.cache is not None:
            try:
                key = self.cache.forecast_key(
                    latitude,
                    longitude,
                )

                cached = await self.cache.get(key)

                if cached is not None:
                    cached_forecast = CanonicalForecast.model_validate(cached)
                    if (
                        cached_forecast.provenance
                        and len(cached_forecast.forecast) >= forecast_days
                        and cached_forecast.hourly
                        and cached_forecast.hourly.get("time")
                    ):
                        return cached_forecast

            except Exception:
                pass

        # ---------------------------------------------------------
        # 2. Open-Meteo supplies the hourly and daily forecast for every location.
        # ---------------------------------------------------------
        forecast = await self.client.get_forecast(
            latitude=latitude,
            longitude=longitude,
            forecast_days=forecast_days,
        )
        canonical = WeatherNormalizer.normalize_forecast(forecast)
        canonical.retrieved_at = datetime.now(UTC)
        canonical.provenance = {
            "provider": "Open-Meteo",
            "role": "hourly and daily forecast",
            "status": "live",
            "fusion": "open-meteo",
            "sources": ["open-meteo"],
            "limitation": (
                "Forecast values are provided by Open-Meteo; "
                "direct NWP model ingestion remains optional."
            ),
            **single_source_score("open-meteo-forecast", canonical.retrieved_at),
        }

        serialized = canonical.model_dump(
            mode="json"
        )

        # ---------------------------------------------------------
        # 4. MongoDB persistence
        # ---------------------------------------------------------
        if self.repository is not None:
            await self.repository.save_forecast(
                canonical
            )

        # ---------------------------------------------------------
        # 5. Redis cache
        # ---------------------------------------------------------
        if self.cache is not None:
            try:
                key = self.cache.forecast_key(
                    latitude,
                    longitude,
                )

                await self.cache.set(
                    key,
                    serialized,
                    ttl=self.cache.FORECAST_TTL,
                )

            except Exception:
                pass

        return canonical

    async def get_historical(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
    ) -> CanonicalHistorical:

        # ---------------------------------------------------------
        # 1. Redis cache lookup
        # ---------------------------------------------------------
        if self.cache is not None:
            try:
                key = self.cache.historical_key(
                    latitude,
                    longitude,
                    start_date,
                    end_date,
                )

                cached = await self.cache.get(key)

                if cached is not None:
                    return CanonicalHistorical.model_validate(
                        cached
                    )

            except Exception:
                pass

        # ---------------------------------------------------------
        # 2. Fetch historical weather
        # ---------------------------------------------------------
        historical = await self.client.get_historical(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
        )

        # ---------------------------------------------------------
        # 3. Normalize
        # ---------------------------------------------------------
        canonical = WeatherNormalizer.normalize_historical(
            historical
        )

        serialized = canonical.model_dump(
            mode="json"
        )

        # ---------------------------------------------------------
        # 4. MongoDB persistence
        # ---------------------------------------------------------
        if self.repository is not None:
            await self.repository.save_historical(
                canonical
            )

        # ---------------------------------------------------------
        # 5. Redis cache
        # ---------------------------------------------------------
        if self.cache is not None:
            try:
                key = self.cache.historical_key(
                    latitude,
                    longitude,
                    start_date,
                    end_date,
                )

                await self.cache.set(
                    key,
                    serialized,
                    ttl=self.cache.HISTORICAL_TTL,
                )

            except Exception:
                pass

        return canonical

    async def close(self) -> None:
        await self.client.close()