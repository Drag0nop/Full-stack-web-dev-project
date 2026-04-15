from app.database.mongodb import db
from datetime import datetime


# 🔹 Save analysis
async def save_analysis(user_email: str, code: str, result: dict):
    collection = db["analyses"]

    document = {
        "user_email": user_email,
        "code": code,
        "result": result,
        "created_at": datetime.utcnow()
    }

    await collection.insert_one(document)


# 🔹 Get user analyses (FIXED + OPTIMIZED)
async def get_user_analyses(user_email: str, limit: int = 10):
    collection = db["analyses"]

    cursor = (
        collection
        .find({"user_email": user_email})
        .sort("created_at", -1)   # 🔥 latest first
        .limit(limit)
    )

    results = []

    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)

    return {
        "count": len(results),
        "analyses": results
    }