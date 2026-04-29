from datetime import datetime

from app.database.mongodb import db


def classify_analysis_result(result: dict):
    result_type = (result or {}).get("type", "")
    if result_type == "readme_summary":
        return "readme_summary"
    if result_type == "error":
        return "failed"
    return "generate_readme"


async def get_user_analysis_stats(user_email: str):
    collection = db["analyses"]
    cursor = collection.find({"user_email": user_email}, {"result": 1})

    stats = {
        "total": 0,
        "generate_readme": 0,
        "readme_summary": 0,
        "failed": 0,
    }

    async for doc in cursor:
        stats["total"] += 1
        classification = classify_analysis_result(doc.get("result", {}))
        if classification == "generate_readme":
            stats["generate_readme"] += 1
        elif classification == "readme_summary":
            stats["readme_summary"] += 1
        elif classification == "failed":
            stats["failed"] += 1

    return stats


async def get_all_user_analysis_stats():
    collection = db["analyses"]
    cursor = collection.find({}, {"user_email": 1, "result": 1})
    stats_by_user = {}

    async for doc in cursor:
        email = doc.get("user_email")
        if not email:
            continue

        if email not in stats_by_user:
            stats_by_user[email] = {
                "total": 0,
                "generate_readme": 0,
                "readme_summary": 0,
                "failed": 0,
            }

        stats_by_user[email]["total"] += 1
        classification = classify_analysis_result(doc.get("result", {}))
        if classification == "generate_readme":
            stats_by_user[email]["generate_readme"] += 1
        elif classification == "readme_summary":
            stats_by_user[email]["readme_summary"] += 1
        elif classification == "failed":
            stats_by_user[email]["failed"] += 1

    return stats_by_user


async def save_analysis(user_email: str, code: str, result: dict):
    collection = db["analyses"]

    document = {
        "user_email": user_email,
        "code": code,
        "result": result,
        "created_at": datetime.utcnow(),
    }

    await collection.insert_one(document)


async def get_user_analyses(user_email: str, page: int = 1, limit: int = 5):
    collection = db["analyses"]
    page = max(page, 1)
    limit = max(min(limit, 50), 1)
    skip = (page - 1) * limit
    total = await collection.count_documents({"user_email": user_email})
    stats = await get_user_analysis_stats(user_email)

    cursor = (
        collection
        .find({"user_email": user_email})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    results = []

    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)

    return {
        "count": len(results),
        "total": total,
        "stats": stats,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total else 1,
        "analyses": results,
    }
