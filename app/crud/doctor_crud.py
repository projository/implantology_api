from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from app.models.doctor import Doctor, DoctorCreate, DoctorUpdate
import math

# Exception class for doctor not found
class DoctorNotFound(Exception):
    pass


async def get_doctor(db: AsyncIOMotorDatabase, doctor_id: str) -> Doctor:
    doctor_data = await db.doctors.find_one({"_id": ObjectId(doctor_id)})
    if doctor_data:
        doctor_data["_id"] = str(doctor_data["_id"])
        return Doctor(**doctor_data)
    raise DoctorNotFound(f"Doctor with id {doctor_id} not found")


async def list_doctors(
    db: AsyncIOMotorDatabase,
    page: int = 1,
    per_page: int = 10,
    search_key: Optional[str] = None
) -> Dict[str, Any]:
    skip = (page - 1) * per_page

    # Build the MongoDB query
    query = {}
    if search_key:
        query = {
            "$or": [
                {"name": {"$regex": search_key, "$options": "i"}},  # Case-insensitive search in name
                # Add more fields here if needed, e.g.:
                # {"description": {"$regex": search_key, "$options": "i"}}
            ]
        }

    # Fetch paginated doctors
    doctors_cursor = db.doctors.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    doctors = await doctors_cursor.to_list(length=per_page)

    # Convert ObjectId to str
    for doctor in doctors:
        doctor["_id"] = str(doctor["_id"])

    # Fetch total number of doctors
    total = await db.doctors.count_documents(query)

    return {
        "data": [Doctor(**doctor).dict() for doctor in doctors],  # Or just return raw doctor dicts if no model
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": math.ceil(total / per_page) if per_page else 0
        }
    }
# async def list_doctors(
#     db: AsyncIOMotorDatabase,
#     page: int = 1,
#     per_page: int = 10,
#     search_key: Optional[str] = None
# ) -> Dict[str, Any]:
#     skip = (page - 1) * per_page

#     # Build the MongoDB query
#     query = {}
#     if search_key:
#         query = {
#             "$or": [
#                 {"name": {"$regex": search_key, "$options": "i"}},  # Case-insensitive search in name
#                 # Add more fields here if needed, e.g.:
#                 # {"description": {"$regex": search_key, "$options": "i"}}
#             ]
#         }

#     # Fetch filtered and paginated doctors
#     doctors_cursor = db.doctors.find(query).sort("created_at", -1).skip(skip).limit(per_page)
#     doctors = await doctors_cursor.to_list(length=per_page)

#     # Convert ObjectId to str
#     for doctor in doctors:
#         doctor["_id"] = str(doctor["_id"])

#     # Total matching documents
#     total = await db.doctors.count_documents(query)

#     return {
#         "data": [Doctor(**doctor).dict() for doctor in doctors],
#         "pagination": {
#             "current_page": page,
#             "per_page": per_page,
#             "total": total,
#             "last_page": math.ceil(total / per_page) if per_page else 0
#         }
#     }


async def create_doctor(db: AsyncIOMotorDatabase, doctor_create: DoctorCreate) -> Doctor:
    doctor_data = doctor_create.dict()
    doctor_data["created_at"] = datetime.now()
    doctor_data["updated_at"] = datetime.now()
    result = await db.doctors.insert_one(doctor_data)
    doctor_data["_id"] = str(result.inserted_id)
    return Doctor(**doctor_data)


async def update_doctor(db: AsyncIOMotorDatabase, doctor_id: str, doctor_update: DoctorUpdate) -> Doctor:
    update_data = {k: v for k, v in doctor_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now()
    result = await db.doctors.update_one({"_id": ObjectId(doctor_id)}, {"$set": update_data})
    if result.modified_count == 1:
        return await get_doctor(db, doctor_id)
    raise DoctorNotFound(f"Doctor with id {doctor_id} not found")


async def delete_doctor(db: AsyncIOMotorDatabase, doctor_id: str):
    result = await db.doctors.delete_one({"_id": ObjectId(doctor_id)})
    if result.deleted_count == 1:
        return True
    raise DoctorNotFound(f"Doctor with id {doctor_id} not found")
