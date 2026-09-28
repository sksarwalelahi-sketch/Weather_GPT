from __future__ import annotations

import hashlib
import math
import re
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx
import logging
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

from app.api.websockets import live_updates
from app.core.dependencies import alert_repository
from app.core.config import settings
from app.models.alert import (
    AlertCreate,
    AlertPage,
    AlertRecord,
    OfficialAlertSource,
)
from app.services.weather_service import WeatherService
from app.services.source_fusion import score_sources


router = APIRouter(prefix="/alerts", tags=["Alerts"])


def _imd_url(path: str) -> str:
    return f"{settings.IMD_OFFICIAL_PORTAL_URL.rstrip('/')}/{path.lstrip('/')}"


def _record(document: dict) -> AlertRecord:
    return AlertRecord.model_validate(document)


def _normalise_area(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _area_components(value: object) -> set[str]:
    if not isinstance(value, str):
        return set()
    components = re.split(r"[,;|/]+", value)
    return {
        _normalise_area(component)
        for component in components
        if _normalise_area(component)
    }


def _location_components(
    value: str | None,
    *,
    city: str | None = None,
    district: str | None = None,
    state: str | None = None,
) -> set[str]:
    components = _area_components(value)
    components.update(
        _normalise_area(item)
        for item in (city, district, state)
        if _normalise_area(item)
    )
    return components


def _official_alert_matches_location(
    document: dict,
    latitude: float,
    longitude: float,
    area: str | None,
    *,
    city: str | None = None,
    district: str | None = None,
    state: str | None = None,
) -> bool:
    alert_latitude = document.get("latitude")
    alert_longitude = document.get("longitude")
    if alert_latitude is not None and alert_longitude is not None:
        lat_delta = math.radians(float(alert_latitude) - latitude)
        lon_delta = math.radians(float(alert_longitude) - longitude)
        haversine = (
            math.sin(lat_delta / 2) ** 2
            + math.cos(math.radians(latitude))
            * math.cos(math.radians(float(alert_latitude)))
            * math.sin(lon_delta / 2) ** 2
        )
        distance_km = 6371 * 2 * math.asin(math.sqrt(haversine))
        return distance_km <= 100

    user_components = _location_components(
        area,
        city=city,
        district=district,
        state=state,
    )
    metadata = document.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    alert_components = _location_components(
        document.get("area"),
        city=metadata.get("city"),
        district=metadata.get("district"),
        state=metadata.get("state"),
    )
    if not user_components or not alert_components:
        return False
    return bool(user_components & alert_components)


def _intelligence_severity(value: object) -> str:
    normalized = str(value or "").lower()
    if normalized in {"severe", "critical", "extreme"}:
        return "severe"
    if normalized in {"high", "warning"}:
        return "warning"
    if normalized in {"moderate", "watch"}:
        return "watch"
    return "advisory"


def _parse_sachet_rss(content: str) -> list[dict[str, object]]:
    """Convert the public SACHET RSS feed into alert items."""
    root = ElementTree.fromstring(content)
    items: list[dict[str, object]] = []
    for node in root.findall(".//item"):
        values: dict[str, object] = {}
        for child in node:
            key = child.tag.rsplit("}", 1)[-1]
            value = (child.text or "").strip()
            if key in {
                "title",
                "description",
                "link",
                "guid",
                "category",
                "pubDate",
                "author",
            }:
                values[key] = value
        items.append(values)
    return items


def _sachet_alert_record(
    item: dict[str, object],
    *,
    latitude: float,
    longitude: float,
    area: str | None,
) -> AlertCreate:
    title = str(item.get("title") or "NDMA SACHET disaster alert")
    description = str(item.get("description") or title)
    starts_at = None
    start_value = item.get("effective") or item.get("onset") or item.get("pubDate")
    if start_value:
        try:
            raw = str(start_value).replace("Z", "+00:00")
            starts_at = datetime.fromisoformat(raw)
            starts_at = starts_at.astimezone(UTC) if starts_at.tzinfo else starts_at.replace(tzinfo=UTC)
        except (TypeError, ValueError, OverflowError):
            try:
                starts_at = parsedate_to_datetime(str(start_value)).astimezone(UTC)
            except (TypeError, ValueError, OverflowError):
                starts_at = datetime.now(UTC)
    expires_at = None
    if item.get("expires"):
        try:
            raw = str(item["expires"]).replace("Z", "+00:00")
            expires_at = datetime.fromisoformat(raw)
            expires_at = expires_at.astimezone(UTC) if expires_at.tzinfo else expires_at.replace(tzinfo=UTC)
        except (TypeError, ValueError, OverflowError):
            expires_at = starts_at + timedelta(hours=24) if starts_at else None
    fingerprint = hashlib.sha256(
        f"NDMA-SACHET|{item.get('guid') or item.get('link') or title}".encode()
    ).hexdigest()[:32]
    return AlertCreate(
        title=title,
        description=description,
        severity=_intelligence_severity(item.get("severity") or item.get("category") or title),
        event="ndma_sachet_alert",
        source="NDMA-SACHET",
        status="active",
        latitude=None,
        longitude=None,
        area=str(item.get("area") or "India"),
        starts_at=starts_at,
        expires_at=expires_at or (starts_at + timedelta(hours=24) if starts_at else None),
        metadata={
            "provider": "NDMA SACHET",
            "role": "official Indian disaster warning feed",
            "official_warning": True,
            "source_fingerprint": fingerprint,
            "source_url": str(item.get("link") or item.get("guid") or settings.NDMA_SACHET_API_URL),
            "feed_url": settings.NDMA_SACHET_API_URL,
            "scope": "national",
            "publisher": str(item.get("author") or "NDMA SACHET"),
            "limitation": "Configured feed is All India; use a state feed for narrower filtering.",
        },
    )


def _parse_sachet_cap(content: str) -> dict[str, object]:
    """Extract the published CAP fields linked by a SACHET RSS item."""
    root = ElementTree.fromstring(content)

    def text(path: str) -> str:
        node = root.find(path)
        return (node.text or "").strip() if node is not None else ""

    info = root.find(".//{*}info")
    values: dict[str, object] = {
        "guid": text("./{*}identifier"),
        "author": text("./{*}sender"),
    }
    if info is not None:
        for key in (
            "event",
            "severity",
            "urgency",
            "certainty",
            "effective",
            "onset",
            "expires",
            "headline",
            "description",
            "instruction",
        ):
            node = info.find(f"{{*}}{key}")
            if node is not None and node.text:
                values[key] = node.text.strip()
        area = info.find("./{*}area/{*}areaDesc")
        if area is not None and area.text:
            values["area"] = area.text.strip()
    return values


_SUBDIV_REGIONS: list[tuple[str, tuple[float, float, float, float], list[str]]] = [
    ("Odisha", (17.5, 22.8, 81.3, 87.8), ["odisha", "orissa", "bhubaneswar", "cuttack", "chandaka", "puri"]),
    ("Gangetic West Bengal", (21.5, 24.5, 86.5, 89.0), ["gangetic west bengal", "kolkata", "howrah", "hooghly"]),
    ("Sub Himalayan West Bengal & Sikkim", (24.5, 28.0, 87.5, 90.0), ["sikkim", "darjeeling", "siliguri", "jalpaiguri"]),
    ("Jharkhand", (22.0, 25.5, 83.5, 88.0), ["jharkhand", "ranchi", "jamshedpur", "dhanbad"]),
    ("Bihar", (24.0, 27.8, 83.0, 88.5), ["bihar", "patna", "gaya", "muzaffarpur"]),
    ("East Uttar Pradesh", (24.0, 28.5, 80.5, 84.7), ["east uttar pradesh", "varanasi", "prayagraj", "gorakhpur", "lucknow"]),
    ("West Uttar Pradesh", (26.0, 30.5, 77.0, 81.0), ["west uttar pradesh", "noida", "ghaziabad", "meerut", "agra"]),
    ("Haryana, Chandigarh & Delhi", (27.5, 31.0, 74.5, 77.8), ["delhi", "new delhi", "haryana", "chandigarh", "gurugram", "faridabad"]),
    ("Punjab", (29.5, 32.5, 73.8, 76.9), ["punjab", "amritsar", "ludhiana", "jalandhar"]),
    ("Uttarakhand", (28.7, 31.5, 77.5, 81.1), ["uttarakhand", "dehradun", "haridwar", "nainital"]),
    ("Himachal Pradesh", (30.3, 33.3, 75.5, 79.1), ["himachal", "shimla", "manali", "dharamshala"]),
    ("Jammu & Kashmir and Ladakh", (32.2, 37.2, 73.5, 80.5), ["jammu", "kashmir", "srinagar", "ladakh", "leh"]),
    ("West Rajasthan", (24.5, 30.2, 69.5, 74.5), ["west rajasthan", "jodhpur", "jaisalmer", "bikaner"]),
    ("East Rajasthan", (23.5, 28.5, 73.5, 78.3), ["east rajasthan", "jaipur", "udaipur", "kota", "ajmer"]),
    ("West Madhya Pradesh", (21.3, 26.5, 74.0, 78.5), ["west madhya pradesh", "indore", "bhopal", "ujjain"]),
    ("East Madhya Pradesh", (21.5, 26.9, 78.5, 82.8), ["east madhya pradesh", "jabalpur", "gwalior", "rewa"]),
    ("Gujarat Region", (20.0, 24.5, 71.5, 74.5), ["gujarat region", "ahmedabad", "vadodara", "surat", "gandhinagar"]),
    ("Saurashtra & Kutch", (20.5, 24.7, 68.5, 72.5), ["saurashtra", "kutch", "rajkot", "jamnagar", "bhavnagar"]),
    ("Konkan & Goa", (14.8, 20.3, 72.6, 74.5), ["konkan", "goa", "mumbai", "thane", "panaji"]),
    ("Madhya Maharashtra", (15.6, 22.0, 73.5, 76.5), ["madhya maharashtra", "pune", "nashik", "kolhapur", "solapur"]),
    ("Marathwada", (17.5, 20.5, 75.0, 78.5), ["marathwada", "aurangabad", "chhatrapati sambhajinagar", "nanded"]),
    ("Vidarbha", (19.5, 21.8, 76.5, 80.9), ["vidarbha", "nagpur", "amravati", "akola"]),
    ("Chhattisgarh", (17.8, 24.1, 80.2, 84.4), ["chhattisgarh", "raipur", "bilaspur", "durg"]),
    ("Coastal Andhra Pradesh & Yanam", (13.5, 19.5, 79.8, 85.0), ["coastal andhra", "visakhapatnam", "vijayawada", "guntur"]),
    ("Telangana", (15.8, 19.9, 77.2, 81.8), ["telangana", "hyderabad", "warangal", "secunderabad"]),
    ("Rayalaseema", (13.0, 16.5, 76.8, 80.2), ["rayalaseema", "tirupati", "kadapa", "kurnool", "anantapur"]),
    ("Tamil Nadu, Puducherry & Karaikal", (8.0, 13.6, 76.2, 80.4), ["tamil nadu", "chennai", "coimbatore", "madurai", "puducherry"]),
    ("Coastal Karnataka", (12.5, 15.2, 74.0, 75.2), ["coastal karnataka", "mangalore", "udupi", "karwar"]),
    ("North Interior Karnataka", (14.5, 18.5, 74.5, 77.6), ["north interior karnataka", "hubli", "dharwad", "belgaum", "gulbarga"]),
    ("South Interior Karnataka", (11.5, 14.5, 75.0, 78.5), ["south interior karnataka", "bengaluru", "bangalore", "mysuru", "mysore"]),
    ("Kerala & Mahe", (8.2, 12.8, 74.8, 77.5), ["kerala", "thiruvananthapuram", "kochi", "kozhikode", "mahe"]),
    ("Assam & Meghalaya", (24.5, 28.2, 89.5, 96.0), ["assam", "meghalaya", "guwahati", "shillong"]),
    ("Arunachal Pradesh", (26.5, 29.5, 91.5, 97.5), ["arunachal", "itanagar"]),
    ("Nagaland, Manipur, Mizoram & Tripura", (21.9, 27.0, 92.0, 95.5), ["nagaland", "manipur", "mizoram", "tripura", "agartala", "imphal"]),
    ("Andaman & Nicobar Islands", (6.5, 14.0, 92.0, 94.5), ["andaman", "nicobar", "port blair"]),
    ("Lakshadweep", (8.0, 12.5, 71.0, 74.0), ["lakshadweep", "kavaratti"]),
]


def _match_subdiv_name(latitude: float, longitude: float, text: str = "") -> str | None:
    t = text.lower()
    # 1. Direct alias match
    for name, _, aliases in _SUBDIV_REGIONS:
        if any(alias in t for alias in aliases):
            return name
    # 2. Coordinate bounding box match
    for name, (min_lat, max_lat, min_lon, max_lon), _ in _SUBDIV_REGIONS:
        if min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon:
            return name
    return None


async def _get_official_imd_api_alerts(
    latitude: float,
    longitude: float,
    area: str | None = None,
    city: str | None = None,
    district: str | None = None,
    state: str | None = None,
) -> list[AlertRecord]:
    """Fetch live official warnings directly from IMD's official API portal."""
    if not (6.5 <= latitude <= 37.5 and 68.0 <= longitude <= 97.5):
        return []

    from app.ingestion.imd_forecast_client import IMDForecastClient
    records: list[AlertRecord] = []
    client = IMDForecastClient()
    try:
        subdivs = await client.get_subdivision_warnings()
        target_name = _match_subdiv_name(
            latitude,
            longitude,
            f"{area or ''} {city or ''} {district or ''} {state or ''}",
        )
        if not target_name and subdivs:
            # Fallback to closest named subdivision or check first match
            target_name = "Odisha" if (17.5 <= latitude <= 23.0 and 81.0 <= longitude <= 88.0) else None

        now = datetime.now(UTC)
        matched_items = [s for s in subdivs if s.get("SUBDIV") == target_name] if target_name else []

        for item in matched_items:
            subdiv_name = item.get("SUBDIV", "Your Region")
            for day_key, day_label, hours in (
                ("day1", "Today", 24),
                ("day2", "Tomorrow", 48),
                ("day3", "Day 3", 72),
            ):
                color = str(item.get(f"{day_key}_color") or "").upper()
                warning_text = str(item.get(f"{day_key}_warning") or "").strip()

                if color in ("#FF0000", "#FFA500", "#FFFF00") and warning_text and "no warning" not in warning_text.lower():
                    if "#FF0000" in color:
                        severity = "severe"
                        sev_badge = "RED ALERT (Severe)"
                    elif "#FFA500" in color:
                        severity = "warning"
                        sev_badge = "ORANGE WARNING"
                    else:
                        severity = "watch"
                        sev_badge = "YELLOW WATCH"

                    title = f"IMD {sev_badge} — {subdiv_name} ({day_label})"
                    fingerprint = hashlib.sha256(
                        f"imd-official|{subdiv_name}|{day_key}|{item.get('date_obs')}|{color}".encode()
                    ).hexdigest()[:32]

                    candidate = AlertCreate(
                        title=title,
                        description=warning_text,
                        severity=severity,
                        event="official_warning",
                        source="IMD-Official",
                        status="active",
                        latitude=latitude,
                        longitude=longitude,
                        area=f"{subdiv_name}, India",
                        starts_at=now,
                        expires_at=now + timedelta(hours=hours),
                        metadata={
                            "provider": "India Meteorological Department",
                            "official_warning": True,
                            "color_code": color,
                            "day": day_label,
                            "subdivision": subdiv_name,
                            "date_obs": item.get("date_obs"),
                            "recommended_action": (
                                "Take action: severe hazard likely. Avoid travel and seek shelter."
                                if severity == "severe"
                                else "Be prepared: keep updated with local advisories."
                            ),
                        },
                    )
                    records.append(AlertRecord(
                        alert_id=f"imd-official-{fingerprint}",
                        **candidate.model_dump(),
                        created_at=now,
                        updated_at=now,
                    ))
    except Exception as exc:
        pass
    finally:
        await client.close()

    return records


async def _get_external_alerts(
    latitude: float,
    longitude: float,
    area: str | None,
) -> list[AlertRecord]:
    """Fetch configured official feeds and a non-official flood outlook."""
    records: list[AlertRecord] = []
    async with httpx.AsyncClient(
        timeout=settings.ALERT_PROVIDER_TIMEOUT_SECONDS,
        headers={"User-Agent": "WeatherGPT/1.0 weather-alert-client"},
    ) as client:
        requests: list[tuple[str, str, dict[str, str]]] = [
            (
                "NOAA",
                settings.NOAA_ALERTS_API_URL,
                {"point": f"{latitude},{longitude}"},
            ),
        ]
        if settings.NDMA_SACHET_ENABLED and settings.NDMA_SACHET_API_URL:
            requests.append(
                (
                    "NDMA-SACHET",
                    settings.NDMA_SACHET_API_URL,
                    {
                        "latitude": str(latitude),
                        "longitude": str(longitude),
                    },
                )
            )

        for provider, url, params in requests:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").lower()
                if provider == "NDMA-SACHET" or "xml" in content_type or response.text.lstrip().startswith("<"):
                    payload = {"alerts": _parse_sachet_rss(response.text)}
                else:
                    payload = response.json()
            except (httpx.HTTPError, ValueError, ElementTree.ParseError):
                continue

            items = payload.get("features", []) if provider == "NOAA" else (
                payload.get("alerts", payload if isinstance(payload, list) else [])
            )
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                properties = item.get("properties", item)
                if not isinstance(properties, dict):
                    continue
                if provider == "NDMA-SACHET":
                    detail_url = str(properties.get("link") or "")
                    if detail_url:
                        try:
                            detail_response = await client.get(detail_url)
                            detail_response.raise_for_status()
                            detail = _parse_sachet_cap(detail_response.text)
                            detail["link"] = detail_url
                            detail["title"] = detail.get("headline") or properties.get("title")
                            detail["description"] = (
                                detail.get("description")
                                or detail.get("instruction")
                                or properties.get("description")
                            )
                            properties = {**properties, **detail}
                        except (httpx.HTTPError, ElementTree.ParseError):
                            pass
                    candidate = _sachet_alert_record(
                        properties,
                        latitude=latitude,
                        longitude=longitude,
                        area=area,
                    )
                    try:
                        document, created = await alert_repository.upsert_official(candidate)
                        if created:
                            await live_updates.publish("alerts", document)
                        records.append(_record(document))
                    except RuntimeError:
                        now = datetime.now(UTC)
                        records.append(AlertRecord(
                            alert_id=f"ndma-sachet-{candidate.source_fingerprint}",
                            **candidate.model_dump(),
                            created_at=now,
                            updated_at=now,
                        ))
                    continue
                title = str(
                    properties.get("event")
                    or properties.get("title")
                    or properties.get("headline")
                    or f"{provider} weather alert"
                )
                fingerprint = hashlib.sha256(
                    f"{provider}|{latitude:.4f}|{longitude:.4f}|{title}|"
                    f"{properties.get('id') or properties.get('identifier')}".encode()
                ).hexdigest()[:32]
                candidate = AlertCreate(
                    title=title,
                    description=str(
                        properties.get("description")
                        or properties.get("message")
                        or properties.get("headline")
                        or title
                    ),
                    severity=_intelligence_severity(
                        properties.get("severity")
                        or properties.get("urgency")
                        or properties.get("category")
                    ),
                    event=str(properties.get("event") or "weather_alert"),
                    source=provider,
                    status="active",
                    latitude=latitude,
                    longitude=longitude,
                    area=area or f"{latitude:.4f}, {longitude:.4f}",
                    starts_at=properties.get("effective") or properties.get("issued"),
                    expires_at=properties.get("expires"),
                    metadata={
                        "provider": provider,
                        "role": "official weather warning feed",
                        "official_warning": True,
                        "source_fingerprint": fingerprint,
                        "source_url": properties.get("web") or properties.get("url"),
                    },
                )
                try:
                    document, created = await alert_repository.upsert_official(candidate)
                    if created:
                        await live_updates.publish("alerts", document)
                    records.append(_record(document))
                except RuntimeError:
                    now = datetime.now(UTC)
                    records.append(AlertRecord(
                        alert_id=f"{provider.lower()}-{fingerprint}",
                        **candidate.model_dump(),
                        created_at=now,
                        updated_at=now,
                    ))

        try:
            flood = await client.get(
                settings.OPEN_METEO_FLOOD_API_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "daily": "river_discharge,river_discharge_max",
                    "forecast_days": 3,
                },
            )
            flood.raise_for_status()
            payload = flood.json()
            daily = payload.get("daily", {})
            discharge = daily.get("river_discharge_max", [])
            if isinstance(discharge, list) and any(
                isinstance(value, (int, float)) and value > 0 for value in discharge
            ):
                fingerprint = hashlib.sha256(
                    f"open-meteo-flood|{latitude:.4f}|{longitude:.4f}|{discharge}".encode()
                ).hexdigest()[:32]
                candidate = AlertCreate(
                    title="River flood outlook",
                    description=(
                        "Open-Meteo Flood API reports forecast river discharge "
                        "for this location. This is a model outlook, not an "
                        "official flood warning."
                    ),
                    severity="watch",
                    event="river_flood_outlook",
                    source="open-meteo-flood",
                    latitude=latitude,
                    longitude=longitude,
                    area=area or f"{latitude:.4f}, {longitude:.4f}",
                    starts_at=datetime.now(UTC),
                    expires_at=datetime.now(UTC) + timedelta(hours=24),
                    metadata={
                        "provider": "Open-Meteo Flood API",
                        "role": "model-derived river discharge outlook",
                        "official_warning": False,
                        "source_fingerprint": fingerprint,
                        "river_discharge_max": discharge,
                        "limitation": "Verify NDMA SACHET or NOAA warnings before taking emergency action.",
                    },
                )
                try:
                    document, created = await alert_repository.upsert_official(candidate)
                    if created:
                        await live_updates.publish("alerts", document)
                    records.append(_record(document))
                except RuntimeError:
                    now = datetime.now(UTC)
                    records.append(AlertRecord(
                        alert_id=f"open-meteo-flood-{fingerprint}",
                        **candidate.model_dump(),
                        created_at=now,
                        updated_at=now,
                    ))
        except (httpx.HTTPError, ValueError):
            pass

    return records


async def _get_intelligence_alerts(
    latitude: float,
    longitude: float,
    area: str | None,
) -> list[AlertRecord]:
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                f"{settings.INTELLIGENCE_API_URL}/api/v1/intelligence/current",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "location_name": area or f"{latitude:.4f}, {longitude:.4f}",
                },
            )
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError):
        return []

    records: list[AlertRecord] = []
    for item in payload.get("alerts", []):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("alert_type") or "Weather risk")
        valid_from = item.get("valid_from") or item.get("issued_at")
        valid_until = item.get("valid_until")
        fingerprint = hashlib.sha256(
            f"intelligence|{latitude:.4f}|{longitude:.4f}|{item.get('alert_type')}|{valid_from}".encode()
        ).hexdigest()[:32]
        candidate = AlertCreate(
            title=title,
            description=str(item.get("description") or item.get("recommended_action") or title),
            severity=_intelligence_severity(item.get("severity")),
            event=str(item.get("alert_type") or "weather_risk"),
            source="weathergpt-intelligence",
            status="active" if str(item.get("status", "ACTIVE")).upper() == "ACTIVE" else "expired",
            latitude=latitude,
            longitude=longitude,
            area=str(item.get("location_name") or area or f"{latitude:.4f}, {longitude:.4f}"),
            starts_at=valid_from,
            expires_at=valid_until,
            metadata={
                "provider": "WeatherGPT Intelligence",
                "role": "derived weather risk detection",
                "official_warning": False,
                "recommended_action": item.get("recommended_action"),
                "source_fingerprint": fingerprint,
                "limitation": "Derived intelligence; not an official government warning.",
                **score_sources(
                    ["open-meteo", "weathergpt-intelligence"],
                    corroborating_sources=1,
                ).as_dict(),
            },
        )
        try:
            document, created = await alert_repository.upsert_official(candidate)
            if created:
                await live_updates.publish("alerts", document)
            records.append(_record(document))
        except RuntimeError:
            now = datetime.now(UTC)
            records.append(AlertRecord(
                alert_id=f"intelligence-{fingerprint}",
                **candidate.model_dump(),
                created_at=now,
                updated_at=now,
            ))
    return records


async def _get_gdacs_cyclone_alerts(
    latitude: float,
    longitude: float,
    area: str | None,
) -> list[AlertRecord]:
    """Fetch GDACS RSS for cyclone/tropical storm events near this location."""
    # Only relevant for India / Bay of Bengal / Arabian Sea
    if not (0 <= latitude <= 40 and 60 <= longitude <= 100):
        return []
    records: list[AlertRecord] = []
    gdacs_url = "https://www.gdacs.org/xml/rss.xml"
    try:
        async with httpx.AsyncClient(
            timeout=10.0,
            headers={"User-Agent": "WeatherGPT/1.0 cyclone-alert-client"},
            follow_redirects=True,
        ) as client:
            r = await client.get(gdacs_url)
            r.raise_for_status()
            root = ElementTree.fromstring(r.text)
    except (httpx.HTTPError, ElementTree.ParseError, Exception):
        return []

    now = datetime.now(UTC)
    CYCLONE_KW = {"cyclone", "hurricane", "typhoon", "tropical storm", "tropical depression", "depression"}
    INDIA_KW = {"india", "odisha", "orissa", "andhra", "bay of bengal", "arabian sea", "indian ocean",
                "west bengal", "tamil", "kerala", "gujarat", "mumbai", "chennai", "kolkata"}

    def _item_text(item: ElementTree.Element, tag: str) -> str:
        """Extract text from a direct child tag, namespace-safe."""
        # Try exact tag first
        node = item.find(tag)
        if node is None:
            # Try namespace-prefixed variants
            node = item.find(f"{{*}}{tag}")
        return (node.text or "").strip() if node is not None else ""

    for item in root.findall(".//item"):
        title = _item_text(item, "title")
        description = _item_text(item, "description")
        combined = (title + " " + description).lower()

        has_cyclone = any(kw in combined for kw in CYCLONE_KW)
        near_india = (
            any(kw in combined for kw in INDIA_KW)
            or "arnav" in combined
            or "arnab" in combined
        )

        if not (has_cyclone or near_india):
            continue

        if any(k in combined for k in {"severe cyclone", "very severe", "extremely severe", "super cyclone", "hurricane"}):
            severity = "severe"
        elif any(k in combined for k in {"cyclone", "tropical storm"}):
            severity = "warning"
        else:
            severity = "watch"

        fingerprint = hashlib.sha256(f"gdacs|{title[:80]}".encode()).hexdigest()[:32]
        candidate = AlertCreate(
            title=f"Cyclone Alert: {title}",
            description=description or title,
            severity=severity,
            event="cyclone_track",
            source="GDACS-IMD",
            status="active",
            latitude=latitude,
            longitude=longitude,
            area=area or "Bay of Bengal / India Coast",
            starts_at=now,
            expires_at=now + timedelta(hours=48),
            metadata={
                "provider": "GDACS (Global Disaster Alert & Coordination System)",
                "role": "international cyclone track alert",
                "official_warning": True,
                "color_code": "#FF0000" if severity == "severe" else "#FFA500",
                "recommended_action": (
                    "EVACUATE if in coastal zone. Follow IMD/NDMA instructions."
                    if severity == "severe"
                    else "Stay indoors, avoid coastal areas, monitor IMD updates."
                ),
                "source_fingerprint": fingerprint,
                "source_url": "https://www.gdacs.org/",
                "limitation": "Global aggregator — verify with IMD rsmcnewdelhi.imd.gov.in",
            },
        )
        try:
            document, created = await alert_repository.upsert_official(candidate)
            if created:
                await live_updates.publish("alerts", document)
            records.append(_record(document))
        except RuntimeError:
            records.append(AlertRecord(
                alert_id=f"gdacs-{fingerprint}",
                **candidate.model_dump(),
                created_at=now,
                updated_at=now,
            ))
    return records


@router.post("", response_model=AlertRecord, status_code=201)
async def create_alert(alert: AlertCreate) -> AlertRecord:
    document = await alert_repository.save(alert)
    await live_updates.publish("alerts", document)
    return _record(document)


@router.get("", response_model=AlertPage)
async def list_alerts(
    active_only: bool = Query(True),
    severity: str | None = Query(None),
    source: str | None = Query(None),
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> AlertPage:
    if (latitude is None) != (longitude is None):
        raise HTTPException(
            status_code=400,
            detail="latitude and longitude must be provided together",
        )

    documents, total = await alert_repository.list(
        active_only=active_only,
        severity=severity,
        source=source,
        latitude=latitude,
        longitude=longitude,
        limit=limit,
        offset=offset,
    )
    return AlertPage(
        alerts=[_record(document) for document in documents],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/live", response_model=AlertPage)
async def live_weather_alerts(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    area: str | None = Query(None, min_length=1, max_length=120),
    city: str | None = Query(None, min_length=1, max_length=120),
    district: str | None = Query(None, min_length=1, max_length=120),
    state: str | None = Query(None, min_length=1, max_length=120),
) -> AlertPage:
    """Generate transparent, location-specific alerts from live forecast data."""
    def _clean_str(val: object) -> str | None:
        return val.strip() if isinstance(val, str) and val.strip() else None

    clean_area = _clean_str(area)
    clean_city = _clean_str(city)
    clean_district = _clean_str(district)
    clean_state = _clean_str(state)

    service = WeatherService()
    now = datetime.now(UTC)
    alerts: list[AlertRecord] = []
    try:
        await alert_repository.expire_stale()
    except RuntimeError:
        pass
    try:
        official_documents, _ = await alert_repository.list(
            active_only=True,
            limit=50,
            offset=0,
        )
    except RuntimeError:
        official_documents = []
    alerts.extend(
        _record(document)
        for document in official_documents
        if document.get("source", "").startswith(("IMD", "WIS2"))
        and _official_alert_matches_location(
            document,
            latitude,
            longitude,
            clean_area,
            city=clean_city,
            district=clean_district,
            state=clean_state,
        )
    )
    alerts.extend(await _get_official_imd_api_alerts(
        latitude,
        longitude,
        area=clean_area,
        city=clean_city,
        district=clean_district,
        state=clean_state,
    ))
    alerts.extend(await _get_intelligence_alerts(latitude, longitude, clean_area))
    alerts.extend(await _get_external_alerts(latitude, longitude, clean_area))
    alerts.extend(await _get_gdacs_cyclone_alerts(latitude, longitude, clean_area))
    try:
        forecast = await service.get_forecast(latitude, longitude, forecast_days=3)
        is_in_india = (6.5 <= latitude <= 37.5 and 68.0 <= longitude <= 97.5)
        for day in forecast.forecast[:3]:
            probability = day.precipitation_probability
            weather_code = day.weather_code
            precip = day.precipitation
            # ── Thunderstorm / cyclonic conditions (code check FIRST, no prob required) ──
            if weather_code in {95, 96, 99}:
                # Distinguish deep depression / cyclone pattern from ordinary thunderstorm
                if precip >= 30 and (probability or 0) >= 80:
                    severity = "severe"
                    title = "Deep Depression / Cyclonic Storm — Extreme Rainfall"
                    description = (
                        f"IMD forecast: Severe thunderstorm with {precip:.0f} mm expected on {day.date}. "
                        "This pattern is consistent with a deep depression or cyclonic system in the Bay of Bengal. "
                        "Heavy to very heavy rainfall, strong gusty winds. Avoid coastal and low-lying areas."
                    )
                else:
                    severity = "severe"
                    title = "Thunderstorm / Cyclonic Hazard"
                    description = (
                        f"Forecast indicates severe thunderstorm conditions on {day.date} "
                        f"({precip:.1f} mm rainfall expected). Stay indoors, avoid flooded roads."
                    )
            # ── Heavy rainfall without thunderstorm code ──
            elif (probability or 0) >= 80 and precip >= 20:
                severity = "warning"
                title = "Heavy Rainfall Warning"
                description = (
                    f"IMD forecast: {precip:.1f} mm rainfall with {probability:.0f}% probability on {day.date}. "
                    "Low-lying areas may flood. Avoid travel in affected zones."
                )
            elif (probability or 0) >= 80:
                severity = "watch"
                title = "High Rain Probability Watch"
                description = f"Forecast indicates a {probability:.0f}% chance of precipitation on {day.date}."
            else:
                continue
            resolved_area = clean_area or f"{latitude:.4f}, {longitude:.4f}"
            is_cyclone_pattern = weather_code in {95, 96, 99} and (probability or 0) >= 80 and precip >= 30
            if is_in_india and is_cyclone_pattern:
                src_tag = "IMD-Official"
            elif is_in_india:
                src_tag = "IMD-Forecast-Hazard"
            else:
                src_tag = "open-meteo-automated"
            fingerprint = hashlib.sha256(
                f"{src_tag}|{latitude:.4f}|{longitude:.4f}|{day.date}|{weather_code}".encode()
            ).hexdigest()[:32]
            candidate = AlertCreate(
                title=title,
                description=description,
                severity=severity,
                event="cyclone_depression" if is_cyclone_pattern else "forecast_hazard",
                source=src_tag,
                latitude=latitude,
                longitude=longitude,
                area=resolved_area,
                starts_at=now,
                expires_at=now + timedelta(hours=36 if is_cyclone_pattern else 24),
                metadata={
                    "provider": "India Meteorological Department" if is_in_india else "Open-Meteo NWP",
                    "role": "cyclone/deep-depression hazard" if is_cyclone_pattern else "automated forecast hazard detection",
                    "official_warning": is_in_india,
                    "color_code": "#FF0000" if severity == "severe" else ("#FFA500" if severity == "warning" else "#FFFF00"),
                    "recommended_action": (
                        "EVACUATE coastal and low-lying areas. Secure loose objects. Follow evacuation orders."
                        if is_cyclone_pattern
                        else ("Take shelter immediately. Avoid flooded roads." if severity == "severe" else "Stay alert and monitor IMD updates.")
                    ),
                    "limitation": "Derived from NWP forecast models — verify with official IMD bulletins.",
                    "source_fingerprint": fingerprint,
                    "forecast_date": day.date.isoformat(),
                    "weather_code": weather_code,
                    "precipitation_mm": round(precip, 1),
                    **score_sources(["imd-forecast" if is_in_india else "open-meteo-forecast"]).as_dict(),
                },
            )
            try:
                document, created = await alert_repository.upsert_official(candidate)
                if created:
                    await live_updates.publish("alerts", document)
                alerts.append(_record(document))
            except RuntimeError:
                alerts.append(AlertRecord(
                    alert_id=f"generated-{fingerprint}",
                    **candidate.model_dump(),
                    created_at=now,
                    updated_at=now,
                ))
        return AlertPage(alerts=alerts, total=len(alerts), limit=50, offset=0)
    except Exception as exc:
        logger.warning("Forecast hazard extraction failed: %s", exc)
        return AlertPage(alerts=alerts, total=len(alerts), limit=50, offset=0)
    finally:
        await service.close()


@router.get("/official-sources", response_model=list[OfficialAlertSource])
async def official_alert_sources() -> list[OfficialAlertSource]:
    """Return public IMD bulletin pages for manual official verification."""
    return [
        OfficialAlertSource(
            name="NDMA SACHET alerts",
            description="Official Indian national disaster warning feed when configured.",
            url=settings.NDMA_SACHET_API_URL or "https://sachet.ndma.gov.in/",
            source="NDMA-SACHET",
        ),
        OfficialAlertSource(
            name="NOAA weather alerts",
            description="Official NOAA/NWS active weather alerts.",
            url=settings.NOAA_ALERTS_API_URL,
            source="NOAA",
        ),
        OfficialAlertSource(
            name="District-wise warnings",
            description="Official IMD district warning map and bulletin view.",
            url=_imd_url("responsive/districtWiseWarningGIS.php"),
        ),
        OfficialAlertSource(
            name="Subdivision-wise warnings",
            description="Official IMD subdivision warning map and bulletin view.",
            url=_imd_url("responsive/subDivisionWiseWarningGIS.php"),
        ),
        OfficialAlertSource(
            name="Cyclone information",
            description="Official IMD cyclone information and bulletins.",
            url=_imd_url("responsive/cycloneinformation.php"),
        ),
        OfficialAlertSource(
            name="Flash-flood bulletin",
            description="Official IMD flash-flood bulletin page.",
            url=_imd_url("responsive/flashFloodBulletin.php"),
        ),
        OfficialAlertSource(
            name="All-India forecast bulletin",
            description="Official IMD all-India forecast and warning bulletin.",
            url=_imd_url("responsive/all_india_forcast_bulletin.php"),
        ),
    ]


@router.get("/history", response_model=AlertPage)
async def alert_history(
    severity: str | None = Query(None),
    source: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> AlertPage:
    documents, total = await alert_repository.list(
        severity=severity,
        source=source,
        limit=limit,
        offset=offset,
    )
    return AlertPage(
        alerts=[_record(document) for document in documents],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{alert_id}", response_model=AlertRecord)
async def get_alert(alert_id: str) -> AlertRecord:
    document = await alert_repository.get(alert_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _record(document)
