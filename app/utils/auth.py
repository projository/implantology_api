from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.config import settings
from app.utils.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta
import bcrypt
import re

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Initialize the JWT secret and algorithm
JWT_SECRET = settings.JWT_SECRET
JWT_ALGORITHM = settings.JWT_ALGORITHM


def generate_jwt(role: str, identifier: str) -> str:
    payload = { 
        "role": role,
        "identifier": identifier,
        "exp": datetime.now() + timedelta(days=30)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_jwt(token: str):
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("identifier") is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    payload = decode_jwt(token)

    # Normalize role
    normalized_role = payload.get("role").strip().upper()

    # Default safe version (for email or other identifiers)
    safe_identifier = re.escape(payload.get("identifier").strip())

    # Normalize phone numbers (handles +91, 0091, 91 prefixes, etc.)
    if re.fullmatch(r"\+?\d+", payload.get("identifier").strip()):  # numeric with optional '+'
        digits = re.sub(r"\D", "", payload.get("identifier"))[-10:]  # keep only last 10 digits
        safe_identifier = f"+91{digits}"

    # Find user by phone or email
    user = await db.users.find_one({
        "role": normalized_role,
        "$or": [
            {"phone_number": {"$regex": f"{re.escape(safe_identifier)}$"}},
            {"email": {"$regex": f"^{re.escape(payload.get("identifier").strip())}$", "$options": "i"}}
        ]
    })

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def admin_required(
    user=Depends(get_current_user)
):
    if user["role"].strip().upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action",
        )
    return user


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))