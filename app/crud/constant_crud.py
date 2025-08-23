from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.constant import Constant, ConstantSet


# Exception class for constant not found
class ConstantNotFound(Exception):
    pass


async def get_constant(db: AsyncIOMotorDatabase) -> Constant:
    constants_cursor = db.constants.find()
    constants = await constants_cursor.to_list(length=100)

    constant_id = None
    for constant in constants:
        constant_id = str(constant.get("_id"))
        if constant_id:  # Check if not None or empty string
            break  # Exit loop after getting the first valid ID

    if not constant_id:
        raise ConstantNotFound("No constant found")

    constant_data = await db.constants.find_one({"_id": ObjectId(constant_id)})
    if constant_data:
        constant_data["_id"] = str(constant_data["_id"])
        return Constant(**constant_data)

    raise ConstantNotFound(f"Constant with id {constant_id} not found")


async def set_constant(db: AsyncIOMotorDatabase, constant_set: ConstantSet) -> Constant:
    constants_cursor = db.constants.find()
    constants = await constants_cursor.to_list(length=100)

    constant_id = None
    for constant in constants:
        constant_id = str(constant.get("_id"))
        if constant_id:  # Check if not None or empty string
            break  # Exit loop after getting the first valid ID

    if not constant_id:
        constant_data = constant_set.dict()
        constant_data["created_at"] = datetime.now()
        constant_data["updated_at"] = datetime.now()
        result = await db.constants.insert_one(constant_data)
        constant_data["_id"] = str(result.inserted_id)
        return Constant(**constant_data)
    else:
        update_data = {k: v for k, v in constant_set.dict().items() if v is not None}
        update_data["updated_at"] = datetime.now()
        result = await db.constants.update_one({"_id": ObjectId(constant_id)}, {"$set": update_data})
        if result.modified_count == 1:
            constant_data = await db.constants.find_one({"_id": ObjectId(constant_id)})
            if constant_data:
                constant_data["_id"] = str(constant_data["_id"])
                return Constant(**constant_data)
        raise ConstantNotFound(f"Constant with id {constant_id} not found")