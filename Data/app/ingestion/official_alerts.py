from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urljoin
from xml.etree import ElementTree

import httpx

from app.models.alert import AlertCreate
from app.services.source_fusion import score_sources


def _first(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def _datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    text = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = parsedate_to_datetime(text)
        except (TypeError, ValueError):
            return None
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _severity(value: Any) -> str:
    text = str(value or "").lower()
    if any(word in text for word in ("extreme", "severe", "red", "emergency")):
        return "severe"
    if any(word in text for word in ("warning", "orange", "high")):
        return "warning"
    if any(word in text for word in ("watch", "yellow", "moderate")):
        return "watch"
    return "advisory"


def _fingerprint(source: str, item: dict[str, Any]) -> str:
    identity = "|".join(str(_first(item, *keys) or "") for keys in (
        ("id", "identifier", "guid", "uri"),
        ("title", "event", "headline"),
        ("sent", "issued", "issue_time", "effective"),
        ("area", "location", "region"),
    ))
    return hashlib.sha256(f"{source}|{identity}".encode()).hexdigest()[:32]


def normalize_official_alert(item: dict[str, Any], *, source: str) -> AlertCreate:
    title = str(_first(item, "title", "headline", "event", "subject") or "Official weather warning")
    description = str(_first(item, "description", "summary", "text", "instruction") or title)
    starts_at = _datetime(_first(item, "starts_at", "effective", "onset", "issued", "sent"))
    expires_at = _datetime(_first(item, "expires_at", "expires", "ends_at"))
    if expires_at is None and starts_at is not None:
        expires_at = starts_at + timedelta(hours=24)
    latitude = _first(item, "latitude", "lat")
    longitude = _first(item, "longitude", "lon", "lng")
    city = _first(item, "city", "city_name", "town")
    district = _first(item, "district", "district_name")
    state = _first(item, "state", "state_name", "province")
    metadata = {
        "official_warning": True,
        "provider": "India Meteorological Department",
        "source_fingerprint": _fingerprint(source, item),
        "source_url": _first(item, "url", "link", "href"),
        "raw_type": "official_bulletin",
        **score_sources([source], official=True).as_dict(),
    }
    for key, value in (
        ("city", city),
        ("district", district),
        ("state", state),
    ):
        if value not in (None, ""):
            metadata[key] = str(value)
    return AlertCreate(
        title=title,
        description=description,
        severity=_severity(_first(item, "severity", "severity_level", "colour", "color", "level")),
        event=str(_first(item, "event", "phenomenon", "category") or "official_weather_warning"),
        source=source,
        latitude=float(latitude) if latitude is not None else None,
        longitude=float(longitude) if longitude is not None else None,
        area=str(_first(item, "area", "areaDesc", "location", "region") or "") or None,
        starts_at=starts_at,
        expires_at=expires_at,
        metadata=metadata,
    )


def normalize_wis2_notification(payload: dict[str, Any]) -> list[AlertCreate]:
    """Normalize a WIS2 notification or embedded CAP-like warning."""
    source = "IMD-WIS2"
    candidates = payload.get("data", payload)
    if isinstance(candidates, dict):
        candidates = candidates.get("alerts", candidates.get("items", candidates))
    if not isinstance(candidates, list):
        candidates = [candidates] if isinstance(candidates, dict) else []
    results: list[AlertCreate] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        provider = str(_first(item, "sender", "source", "provider", "origin") or "").lower()
        if provider and not any(value in provider for value in ("imd", "india", "inmet")):
            continue
        alert = normalize_official_alert(item, source=source)
        links = payload.get("links", []) if isinstance(payload.get("links"), list) else []
        if links and not alert.metadata.get("source_url"):
            canonical = next((link.get("href") for link in links if isinstance(link, dict) and link.get("href")), None)
            alert.metadata["source_url"] = canonical
        results.append(alert)
    return results


class OfficialIMDWarningClient:
    """
    Polls the official IMD warning/forecast-warning endpoint (cityforecastwarning
    or districtwarning) for new alerts and converts them to AlertCreate objects.

    Authentication uses IMDAuthManager (X-API-KEY + JWT Bearer).
    Falls back to legacy bare-token auth if IMD_DEV_KEY_2 is not configured.
    """

    def __init__(
        self,
        url: str,
        api_key: str = "",
        timeout: float = 30.0,
    ):
        self.url = url
        self.api_key = api_key
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        # Use new auth manager when the official key is available
        self._auth: Any | None = None
        if api_key:
            try:
                from app.ingestion.imd_auth import IMDAuthManager
                from app.core.config import settings
                self._auth = IMDAuthManager(
                    api_key=api_key,
                    email=settings.IMD_EMAIL,
                    password=settings.IMD_PASSWORD,
                )
            except Exception:
                self._auth = None

    async def _get_headers(self) -> dict[str, str]:
        if self._auth is not None:
            try:
                return await self._auth.get_headers()
            except Exception:
                pass
        # Fallback: legacy Bearer token
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}

    async def fetch(self) -> list[AlertCreate]:
        headers = await self._get_headers()
        response = await self.client.get(self.url, headers=headers)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "xml" in content_type or response.text.lstrip().startswith("<"):
            root = ElementTree.fromstring(response.text)
            items = []
            for node in root.findall(".//item") + root.findall(".//alert"):
                items.append({child.tag.rsplit("}", 1)[-1]: child.text or "" for child in node})
        else:
            payload = response.json()
            items = payload if isinstance(payload, list) else payload.get("alerts", payload.get("items", [payload]))
        return [
            normalize_official_alert(item, source="IMD-official-feed")
            for item in items
            if isinstance(item, dict)
        ]

    async def close(self) -> None:
        await self.client.aclose()
        if self._auth is not None:
            await self._auth.close()

