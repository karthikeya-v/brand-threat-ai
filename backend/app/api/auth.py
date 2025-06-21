from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.db.database import get_db
from app.core.auth import (
    authenticate_user, 
    create_access_token, 
    get_password_hash, 
    get_current_active_user,
    get_user_by_email
)
from app.models.user import User

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    company_name: Optional[str] = None
    tier: str = "starter"


class UserResponse(BaseModel):
    id: str
    email: str
    company_name: Optional[str]
    tier: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class TokenRefresh(BaseModel):
    access_token: str


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        company_name=user_data.company_name,
        tier=user_data.tier
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=str(user.id),
            email=user.email,
            company_name=user.company_name,
            tier=user.tier,
            is_active=user.is_active,
            created_at=user.created_at.isoformat()
        )
    }


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=str(user.id),
            email=user.email,
            company_name=user.company_name,
            tier=user.tier,
            is_active=user.is_active,
            created_at=user.created_at.isoformat()
        )
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        company_name=current_user.company_name,
        tier=current_user.tier,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat()
    )


@router.post("/refresh", response_model=TokenRefresh)
async def refresh_token(
    current_user: User = Depends(get_current_active_user)
):
    access_token = create_access_token(data={"sub": str(current_user.id)})
    return {"access_token": access_token}


@router.post("/logout")
async def logout():
    # In a real implementation, you might want to blacklist the token
    return {"message": "Successfully logged out"}