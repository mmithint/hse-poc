from typing import Optional
from db import get_db


async def save_upload(doc: dict) -> str:
    db = get_db()
    result = await db["uploads"].insert_one(doc)
    return str(result.inserted_id)


async def update_summaries(
    upload_id: str,
    user_summary: str,
    manager_summary: str,
) -> None:
    db = get_db()
    await db["uploads"].update_one(
        {"_id": upload_id},
        {"$set": {"user_summary": user_summary, "manager_summary": manager_summary}},
    )


async def get_all_uploads() -> list[dict]:
    db = get_db()
    cursor = db["uploads"].find(
        {},
        {
            "_id": 1,
            "filename": 1,
            "uploaded_by": 1,
            "upload_date": 1,
            "date_range": 1,
            "total_observations": 1,
            "user_summary": 1,
            "manager_summary": 1,
        },
    ).sort("upload_date", -1)
    return await cursor.to_list(length=None)


async def get_upload_by_id(upload_id: str) -> Optional[dict]:
    db = get_db()
    return await db["uploads"].find_one({"_id": upload_id})
