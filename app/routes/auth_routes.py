from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from app.models.pagination import PaginatedResponse
from app.models.user import (
    User,
    UserCreate,
    UserUpdate,
)
from app.crud.user_crud import (
    list_users,
    create_user,
    get_user,
    update_user,
    delete_user,
    UserNotFound,
)
from app.utils.database import get_database
from app.utils.auth import admin_required, generate_jwt, get_current_user, verify_password

router = APIRouter()

# Dependency to get the database
async def get_db():
    db = await get_database()
    return db


@router.get("/users", response_model=PaginatedResponse[User])
async def list_all_users(
    role: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    keyword: str = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user=Depends(admin_required)
):
    users = await list_users(db, role, page, per_page, keyword)
    return users


@router.post("/register", response_model=dict)
async def register(
    user: UserCreate, 
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    existing_user_by_phone = await db.users.find_one({"phone_number": user.phone_number, "role": user.role})
    if existing_user_by_phone:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User with this phone number already exists",
        )

    existing_user_by_email = await db.users.find_one({"email": user.email, "role": user.role})
    if existing_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User with this email already exists",
        )
    
    created_user = await create_user(db, user)
    if not created_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register a user"
        )

    return {"token": generate_jwt(user.role, user.phone_number)}


class LoginRequest(BaseModel):
    role: str
    phone_number: str
    password: str

@router.post("/login", response_model=dict)
async def login(
    body: LoginRequest, 
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    existing_user = await db.users.find_one({"role": body.role, "phone_number": body.phone_number})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not verify_password(body.password, existing_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    return {"token": generate_jwt(body.role, body.phone_number)}


@router.get("/me", response_model=User)
async def get_current_profile(current_user: User = Depends(get_current_user)):
    current_user["_id"] = str(current_user["_id"])
    return User(**current_user)

@router.put("/me", response_model=User)
async def update_current_profile(
    user_update: UserUpdate, 
    db: AsyncIOMotorDatabase = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    try:
        updated_user = await update_user(db, str(current_user["_id"]), user_update)
        return updated_user
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))