from __future__ import annotations

import json
import logging
import time
from collections import Counter
from threading import Lock
from typing import Any


class JsonFormatter(logging.Formatter):
    """Render application logs as one structured JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        event = getattr(record, "event", None)
        if event is not None:
            payload["event"] = event
        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            payload.update(fields)
        return json.dumps(payload, default=str, separators=(",", ":"))


def configure_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            handler.setFormatter(JsonFormatter())
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(logging.INFO)


class Metrics:
    def __init__(self) -> None:
        self._counts: Counter[str] = Counter()
        self._lock = Lock()
        self._started_at = time.time()

    def increment(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._counts[name] += amount

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            counters = dict(self._counts)
        return {
            "uptime_seconds": round(time.time() - self._started_at, 3),
            "counters": counters,
        }


metrics = Metrics()
