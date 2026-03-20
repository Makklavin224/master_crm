from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.security import decode_access_token, validate_tg_init_data
from app.models.master import Master

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login", auto_error=False
)


async def get_db():
    """Yield a database session, rollback on error."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_master(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Master:
    """Decode JWT, load master from DB, raise 401 if invalid."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        master_id: str | None = payload.get("sub")
        if master_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    async with async_session_factory() as db:
        result = await db.execute(
            select(Master).where(Master.id == UUID(master_id))
        )
        master = result.scalar_one_or_none()
        if master is None or not master.is_active:
            raise credentials_exception
        return master


async def get_db_with_rls(
    session: Annotated[AsyncSession, Depends(get_db)],
    master: Annotated[Master, Depends(get_current_master)],
) -> AsyncSession:
    """Set RLS context for the current master. Uses SET LOCAL (transaction-scoped)."""
    # SET LOCAL does not support parameterized values in asyncpg.
    # Safe: master.id is a UUID parsed from a verified JWT, not user input.
    await session.execute(
        text(f"SET LOCAL app.current_master_id = '{master.id}'"),
    )
    return session


async def get_current_client_from_initdata(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Validate TG initData from X-Init-Data header.
    Returns parsed user info dict (tg user_id, first_name, etc.).
    Raises 401 if invalid.
    """
    init_data_raw = request.headers.get("X-Init-Data")
    if not init_data_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Init-Data header",
        )

    user_data = validate_tg_init_data(init_data_raw, settings.tg_bot_token)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram auth data",
        )

    return user_data


async def get_optional_master(
    token: Annotated[str | None, Depends(oauth2_scheme_optional)],
) -> Master | None:
    """
    Try JWT auth, return Master or None.
    Used by dual-auth endpoints (master OR client).
    """
    if token is None:
        return None

    try:
        payload = decode_access_token(token)
        master_id: str | None = payload.get("sub")
        if master_id is None:
            return None
    except InvalidTokenError:
        return None

    async with async_session_factory() as db:
        result = await db.execute(
            select(Master).where(Master.id == UUID(master_id))
        )
        master = result.scalar_one_or_none()
        if master is None or not master.is_active:
            return None
        return master
