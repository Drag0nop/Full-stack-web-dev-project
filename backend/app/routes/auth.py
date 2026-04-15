from fastapi import APIRouter, HTTPException
from app.models.user import User
from app.services.auth_service import register_user, authenticate_user

router = APIRouter(tags=["auth"])


@router.post("/register")
async def register(user: User):
    result = await register_user(user)

    if not result:
        raise HTTPException(status_code=400, detail="User already exists")

    return {"message": "User registered successfully"}


@router.post("/login")
async def login(user: User):
    token = await authenticate_user(user)

    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "access_token": token,
        "token_type": "bearer"
    }