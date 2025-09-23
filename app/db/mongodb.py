"""MongoDB client helpers."""
from __future__ import annotations

from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


class MongoDB:
    """Simple wrapper around :class:`AsyncIOMotorClient`."""

    def __init__(self, uri: str, db_name: str) -> None:
        self._client = AsyncIOMotorClient(uri)
        self._db: AsyncIOMotorDatabase = self._client[db_name]

    @property
    def database(self) -> AsyncIOMotorDatabase:
        """Return the active database instance."""

        return self._db

    async def ensure_admin(self, admin_id: int) -> None:
        """Ensure that an admin document exists with the provided identifier."""

        await self._db.admins.update_one(
            {"_id": admin_id},
            {
                "$setOnInsert": {
                    "created_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )

    def close(self) -> None:
        """Close the MongoDB client."""

        self._client.close()
