from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.security import decode_access_token
from app.models.master import Master

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


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
    db: Annotated[AsyncSession, Depends(get_db)],
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
    await session.execute(
        text("SET LOCAL app.current_master_id = :master_id"),
        {"master_id": str(master.id)},
    )
    return session
