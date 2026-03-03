# app/utils/database.py

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from app.core.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db = None


async def connect_to_mongo():
    global _client, _db

    if _client is None:
        logger.info("Connecting to MongoDB...")

        _client = AsyncIOMotorClient(
            settings.DATABASE_URL,
            server_api=ServerApi("1"),
            maxPoolSize=50,          # production pool size
            minPoolSize=5,
        )

        _db = _client[settings.DATABASE_NAME]

        # Test connection
        await _client.admin.command("ping")

        logger.info("MongoDB connection established.")


async def close_mongo_connection():
    global _client

    if _client:
        logger.info("Closing MongoDB connection...")
        _client.close()
        logger.info("MongoDB connection closed.")


async def get_database():
    if _db is None:
        await connect_to_mongo()
    return _db


# -----------------------------------------
# Index Creation
# -----------------------------------------

async def create_indexes():
    db = await get_database()

    logger.info("Creating MongoDB indexes...")

    # Property Categories
    await db.property_categories.create_index("name", unique=True)

    # Intent indexes
    await db.intents.create_index("intent", unique=True)
    await db.intents.create_index("created_at")
    await db.intents.create_index("priority")
    await db.intents.create_index("is_active")

    logger.info("Indexes ensured successfully.")