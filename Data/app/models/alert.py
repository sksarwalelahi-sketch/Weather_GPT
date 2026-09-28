from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""
    severity: str = "unknown"
    event: str | None = None
    source: str = "api"
    status: str = "active"
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    area: str | None = None
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def source_fingerprint(self) -> str | None:
        value = self.metadata.get("source_fingerprint")
        return value if isinstance(value, str) and value else None


class AlertRecord(AlertCreate):
    alert_id: str
    created_at: datetime
    updated_at: datetime


class AlertPage(BaseModel):
    alerts: list[AlertRecord]
    total: int
    limit: int
    offset: int


class OfficialAlertSource(BaseModel):
    name: str
    description: str
    url: str
    source: str = "IMD"
    official: bool = True
