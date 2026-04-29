from app.database.mongodb import get_user_collection
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.services.analysis_service import get_all_user_analysis_stats


async def ensure_default_admin():
    users = get_user_collection()

    existing = await users.find_one({"email": settings.ADMIN_EMAIL})
    if existing:
        if existing.get("role") != "admin":
            await users.update_one(
                {"_id": existing["_id"]},
                {"$set": {"role": "admin"}}
            )
        return

    await users.insert_one({
        "email": settings.ADMIN_EMAIL,
        "password": hash_password(settings.ADMIN_PASSWORD),
        "role": "admin"
    })


async def register_user(user):
    users = get_user_collection()

    existing = await users.find_one({"email": user.email})
    if existing:
        return None

    user_data = user.dict()
    user_data["password"] = hash_password(user.password)
    user_data["role"] = "user"
    await users.insert_one(user_data)

    return True


async def authenticate_user(user):
    users = get_user_collection()

    existing = await users.find_one({"email": user.email})
    if not existing:
        return None

    if not verify_password(user.password, existing["password"]):
        return None

    token = create_access_token({
        "sub": user.email,
        "role": existing.get("role", "user")
    })

    return token


async def get_all_users():
    users = get_user_collection()
    cursor = users.find({"role": {"$ne": "admin"}}, {"password": 0}).sort("email", 1)
    stats_by_user = await get_all_user_analysis_stats()
    results = []

    async for user in cursor:
        user["_id"] = str(user["_id"])
        user["usageStats"] = stats_by_user.get(
            user.get("email", ""),
            {
                "total": 0,
                "generate_readme": 0,
                "readme_summary": 0,
                "failed": 0,
            }
        )
        results.append(user)

    return {
        "count": len(results),
        "users": results
    }
