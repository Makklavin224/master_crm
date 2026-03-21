from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    DUMMY_HASH,
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.master import Master


async def register_master(
    db: AsyncSession, email: str, password: str, name: str
) -> tuple[Master, str]:
    """Register a new master with email+password. Returns (master, access_token)."""
    # Validate
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )
    email_lower = email.lower().strip()
    if not email_lower or "@" not in email_lower:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address",
        )

    # Check uniqueness
    result = await db.execute(
        select(Master).where(Master.email == email_lower)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create master
    master = Master(
        email=email_lower,
        hashed_password=hash_password(password),
        name=name.strip(),
    )
    db.add(master)
    await db.flush()  # Get the generated UUID

    token = create_access_token(data={"sub": str(master.id)})
    return master, token


PLATFORM_COLUMN_MAP = {
    "telegram": "tg_user_id",
    "max": "max_user_id",
    "vk": "vk_user_id",
}


async def register_master_from_bot(
    db: AsyncSession,
    name: str,
    email: str,
    platform: str,
    platform_user_id: str,
) -> tuple[Master, str]:
    """Register a new master from a bot interaction (no password).

    Returns (master, access_token).
    """
    email_lower = email.lower().strip()
    if not email_lower or "@" not in email_lower:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address",
        )

    # Check email uniqueness
    result = await db.execute(
        select(Master).where(Master.email == email_lower)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Check platform_user_id uniqueness
    column_name = PLATFORM_COLUMN_MAP.get(platform)
    if not column_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported platform: {platform}",
        )

    column = getattr(Master, column_name)
    result = await db.execute(
        select(Master).where(column == platform_user_id)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Platform account already linked to another master",
        )

    # Create master with platform binding (no password)
    master = Master(
        email=email_lower,
        name=name.strip(),
        **{column_name: platform_user_id},
    )
    db.add(master)
    await db.flush()

    token = create_access_token(data={"sub": str(master.id)})
    return master, token


async def authenticate_master(
    db: AsyncSession, email: str, password: str
) -> tuple[Master, str]:
    """Authenticate a master with email+password. Returns (master, access_token)."""
    email_lower = email.lower().strip()
    result = await db.execute(
        select(Master).where(Master.email == email_lower)
    )
    master = result.scalar_one_or_none()

    if master is None:
        # Timing attack prevention: hash dummy password even when user not found
        verify_password("dummy", DUMMY_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(password, master.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not master.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    token = create_access_token(data={"sub": str(master.id)})
    return master, token
