from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_master, get_db
from app.core.security import create_access_token, validate_tg_init_data
from app.models.master import Master
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TgAuthRequest,
    TokenResponse,
)
from app.schemas.master import MasterRead
from app.services.auth_service import authenticate_master, register_master

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: RegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]
):
    master, token = await register_master(db, data.email, data.password, data.name)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]
):
    master, token = await authenticate_master(db, data.email, data.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MasterRead)
async def get_me(
    current_master: Annotated[Master, Depends(get_current_master)],
):
    return current_master


@router.post("/tg", response_model=TokenResponse)
async def tg_auth(
    data: TgAuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Exchange valid Telegram initData for a JWT.

    Validates the HMAC-SHA256 signature, extracts tg user_id,
    looks up the Master by tg_user_id, and returns a JWT.
    """
    user_data = validate_tg_init_data(data.init_data, settings.tg_bot_token)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram auth data",
        )

    tg_user_id = str(user_data.get("id", ""))
    if not tg_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram auth data",
        )

    result = await db.execute(
        select(Master).where(
            Master.tg_user_id == tg_user_id,
            Master.is_active.is_(True),
        )
    )
    master = result.scalar_one_or_none()
    if master is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master account not linked to this Telegram user",
        )

    token = create_access_token(data={"sub": str(master.id)})
    return TokenResponse(access_token=token)
