from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# Create client with timeout (important)
client = AsyncIOMotorClient(
    settings.MONGO_URI,
    serverSelectionTimeoutMS=5000
)

# Select DB
db = client[settings.DB_NAME]


# 🔹 Collections
def get_user_collection():
    return db["users"]


def get_analysis_collection():
    return db["analyses"]