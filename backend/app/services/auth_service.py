from app.database.mongodb import get_user_collection
from app.core.security import hash_password, verify_password, create_access_token


async def register_user(user):
    users = get_user_collection()

    existing = await users.find_one({"email": user.email})
    if existing:
        return None

    user.password = hash_password(user.password)
    await users.insert_one(user.dict())

    return True


async def authenticate_user(user):
    users = get_user_collection()

    existing = await users.find_one({"email": user.email})
    if not existing:
        return None

    if not verify_password(user.password, existing["password"]):
        return None

    token = create_access_token({"sub": user.email})

    return token