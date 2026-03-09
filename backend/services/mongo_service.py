from typing import Optional
from db import get_db


async def save_upload(doc: dict) -> str:
    db = get_db()
    result = await db["hse_poc"].insert_one(doc)
    return str(result.inserted_id)


async def update_summaries(
    upload_id: str,
    user_summary: str,
    manager_summary: str,
    detailed_summary: str = "",
    interventions_by_facility: dict = None,
    total_interventions: int = 0,
    category_analysis: list = None,
) -> None:
    db = get_db()
    update_fields = {
        "user_summary": user_summary,
        "manager_summary": manager_summary,
        "detailed_summary": detailed_summary,
        "chart_data.interventions_by_facility": interventions_by_facility or {},
        "chart_data.total_interventions": total_interventions,
        "category_analysis": category_analysis or [],
    }
    await db["hse_poc"].update_one(
        {"_id": upload_id},
        {"$set": update_fields},
    )


async def get_all_uploads() -> list[dict]:
    db = get_db()
    cursor = db["hse_poc"].find(
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
            "detailed_summary": 1,
        },
    ).sort("upload_date", -1)
    return await cursor.to_list(length=None)


async def get_upload_by_id(upload_id: str) -> Optional[dict]:
    db = get_db()
    return await db["hse_poc"].find_one({"_id": upload_id})


async def delete_upload(upload_id: str) -> int:
    db = get_db()
    result = await db["hse_poc"].delete_one({"_id": upload_id})
    return result.deleted_count
