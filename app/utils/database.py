from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from app.core.config import settings

client = AsyncIOMotorClient(settings.DATABASE_URL, server_api=ServerApi("1"))
db = client[settings.DATABASE_NAME]


async def get_database():
    return db


# Ensure unique index on 'name' field for property_categories
async def create_indexes():
    await db.property_categories.create_index("name", unique=True)
