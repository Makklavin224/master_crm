from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_master, get_db
from app.models.master import Master
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
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
