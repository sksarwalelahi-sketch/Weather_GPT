from __future__ import annotations

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
)

from app.core.config import settings


class MongoDB:
    def __init__(
        self,
        uri: str | None = None,
        database_name: str | None = None,
    ):
        self.uri = (
            uri
            if uri is not None
            else settings.MONGODB_URI
        )

        self.database_name = (
            database_name
            if database_name is not None
            else settings.MONGODB_DATABASE
        )

        self.client = None
        self.database = None

    async def connect(self):
        if self.client is not None:
            return

        self.client = AsyncIOMotorClient(
            self.uri,
            serverSelectionTimeoutMS=5000,
        )

        self.database = self.client[
            self.database_name
        ]

    async def disconnect(self):
        if self.client is not None:
            self.client.close()

        self.client = None
        self.database = None

    def get_database(
        self,
    ) -> AsyncIOMotorDatabase:
        if self.database is None:
            raise RuntimeError(
                "MongoDB is not connected"
            )

        return self.database

    async def ping(self) -> bool:
        if self.client is None:
            await self.connect()

        try:
            await self.client.admin.command(
                "ping"
            )
            return True

        except Exception as exc:
            print(
                f"MongoDB ping failed: {exc}"
            )
            return False


mongodb = MongoDB()