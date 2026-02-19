import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(
            os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
        )
    return _client


def get_db() -> AsyncIOMotorDatabase:
    return get_client()[os.environ.get("MONGODB_DB", "Oxy")]


async def close_client() -> None:
    global _client
    if _client:
        _client.close()
        _client = None
