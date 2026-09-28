from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.database.mongodb import MongoDB
from app.models.alert import AlertCreate


class MongoAlertRepository:
    COLLECTION = "alerts"

    def __init__(self, mongodb: MongoDB):
        self.mongodb = mongodb

    async def save(self, alert: AlertCreate) -> dict[str, Any]:
        now = datetime.now(UTC)
        document = alert.model_dump(mode="python")
        document.update(
            {
                "alert_id": str(uuid4()),
                "created_at": now,
                "updated_at": now,
            }
        )
        await self.mongodb.get_database()[
            self.COLLECTION
        ].insert_one(document)
        return document

    async def upsert_official(self, alert: AlertCreate) -> tuple[dict[str, Any], bool]:
        fingerprint = alert.source_fingerprint
        if not fingerprint:
            return await self.save(alert), True
        collection = self.mongodb.get_database()[self.COLLECTION]
        now = datetime.now(UTC)
        document = alert.model_dump(mode="python")
        existing = await collection.find_one(
            {"metadata.source_fingerprint": fingerprint},
            {"_id": 0},
        )
        if existing:
            await collection.update_one(
                {"alert_id": existing["alert_id"]},
                {"$set": {**document, "updated_at": now}},
            )
            existing.update(document)
            existing["updated_at"] = now
            return existing, False
        document.update({
            "alert_id": f"official-{fingerprint}",
            "created_at": now,
            "updated_at": now,
        })
        await collection.insert_one(document)
        return document, True

    async def expire_stale(self) -> int:
        now = datetime.now(UTC)
        result = await self.mongodb.get_database()[self.COLLECTION].update_many(
            {
                "status": "active",
                "expires_at": {"$ne": None, "$lte": now},
            },
            {
                "$set": {
                    "status": "expired",
                    "updated_at": now,
                }
            },
        )
        return result.modified_count

    async def get(
        self,
        alert_id: str,
    ) -> dict[str, Any] | None:
        return await self.mongodb.get_database()[
            self.COLLECTION
        ].find_one(
            {"alert_id": alert_id},
            {"_id": 0},
        )

    async def list(
        self,
        *,
        active_only: bool = False,
        severity: str | None = None,
        source: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        query: dict[str, Any] = {}
        if active_only:
            now = datetime.now(UTC)
            query["status"] = "active"
            query["$or"] = [
                {"expires_at": None},
                {"expires_at": {"$gt": now}},
            ]
            query["$and"] = [
                {
                    "$or": [
                        {"starts_at": None},
                        {"starts_at": {"$lte": now}},
                    ]
                }
            ]
        if severity:
            query["severity"] = severity
        if source:
            query["source"] = source
        if latitude is not None:
            query["latitude"] = latitude
        if longitude is not None:
            query["longitude"] = longitude

        collection = self.mongodb.get_database()[self.COLLECTION]
        total = await collection.count_documents(query)
        cursor = (
            collection.find(query, {"_id": 0})
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )
        return [document async for document in cursor], total

    async def ensure_indexes(self) -> None:
        collection = self.mongodb.get_database()[self.COLLECTION]
        await collection.create_index(
            [("alert_id", 1)],
            unique=True,
        )
        await collection.create_index(
            [("metadata.source_fingerprint", 1)],
            unique=True,
            sparse=True,
        )
        await collection.create_index(
            [("status", 1), ("expires_at", 1), ("created_at", -1)]
        )
        await collection.create_index(
            [
                ("latitude", 1),
                ("longitude", 1),
                ("created_at", -1),
            ]
        )
