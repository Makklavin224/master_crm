import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_master, get_db
from app.core.security import (
    create_access_token,
    validate_max_init_data,
    validate_tg_init_data,
    validate_vk_launch_params,
)
from app.models.master import Master
from app.models.qr_session import QrSession
from app.schemas.auth import (
    BotRegisterRequest,
    LinkAccountRequest,
    LoginRequest,
    MagicLinkVerifyRequest,
    MaxAuthRequest,
    QrConfirmRequest,
    QrInitResponse,
    QrStatusResponse,
    RegisterRequest,
    TgAuthRequest,
    TokenResponse,
    VkAuthRequest,
)
from app.schemas.master import MasterRead
from app.services.auth_service import (
    PLATFORM_COLUMN_MAP,
    authenticate_master,
    register_master,
    register_master_from_bot,
)

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


@router.post("/max", response_model=TokenResponse)
async def max_auth(
    data: MaxAuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Exchange valid MAX initData for a JWT.

    Validates the HMAC-SHA256 signature (identical algorithm to Telegram),
    extracts MAX user_id, looks up the Master by max_user_id, and returns a JWT.
    """
    user_data = validate_max_init_data(data.init_data, settings.max_bot_token)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MAX auth data",
        )

    max_user_id = str(user_data.get("id", ""))
    if not max_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MAX auth data",
        )

    result = await db.execute(
        select(Master).where(
            Master.max_user_id == max_user_id,
            Master.is_active.is_(True),
        )
    )
    master = result.scalar_one_or_none()
    if master is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master account not linked to this MAX user",
        )

    token = create_access_token(data={"sub": str(master.id)})
    return TokenResponse(access_token=token)


@router.post("/vk", response_model=TokenResponse)
async def vk_auth(
    data: VkAuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Exchange valid VK launch params for a JWT.

    Validates the HMAC-SHA256 signature on vk_* params,
    extracts vk_user_id, looks up the Master by vk_user_id, and returns a JWT.
    """
    params = validate_vk_launch_params(
        data.launch_params, settings.vk_app_secret
    )
    if params is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid VK auth data",
        )

    vk_user_id = params.get("vk_user_id", "")
    if not vk_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid VK auth data",
        )

    result = await db.execute(
        select(Master).where(
            Master.vk_user_id == vk_user_id,
            Master.is_active.is_(True),
        )
    )
    master = result.scalar_one_or_none()
    if master is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master account not linked to this VK user",
        )

    token = create_access_token(data={"sub": str(master.id)})
    return TokenResponse(access_token=token)


# --- QR Code Login Flow ---


@router.post("/qr/init", response_model=QrInitResponse)
async def qr_init(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Create a QR login session. No auth required.

    Returns session_id and qr_payload (deep link to TG bot).
    Frontend renders qr_payload as QR code and polls /qr/status.
    """
    session_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    # Bot username for deep link
    bot_username = "MasterCRMBot"
    if settings.tg_bot_token:
        # Will be resolved at runtime; for now use a sensible default
        bot_username = "MasterCRMBot"

    qr_payload = f"https://t.me/{bot_username}?start=qr_{session_id}"

    session = QrSession(
        id=uuid.UUID(session_id),
        session_type="qr",
        token=session_id,
        status="pending",
        expires_at=expires_at,
    )
    db.add(session)
    await db.flush()

    return QrInitResponse(session_id=session_id, qr_payload=qr_payload)


@router.get("/qr/status/{session_id}", response_model=QrStatusResponse)
async def qr_status(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Check QR session status. No auth required.

    Polled by the frontend every 3 seconds.
    Returns 'pending', 'confirmed' (with access_token), or 'expired'.
    """
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID",
        )

    result = await db.execute(
        select(QrSession).where(QrSession.id == sid)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    now = datetime.now(timezone.utc)
    if session.status == "pending" and now > session.expires_at:
        session.status = "expired"
        await db.flush()
        return QrStatusResponse(status="expired")

    if session.status == "confirmed":
        return QrStatusResponse(
            status="confirmed", access_token=session.access_token
        )

    return QrStatusResponse(status=session.status)


@router.post("/qr/confirm")
async def qr_confirm(
    data: QrConfirmRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Confirm a QR login session. Called by the bot (not the web panel).

    The bot calls this when a user sends /start qr_{session_id}.
    Looks up the master by tg_user_id, creates a JWT, marks session confirmed.
    """
    try:
        sid = uuid.UUID(data.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID",
        )

    result = await db.execute(
        select(QrSession).where(QrSession.id == sid)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    now = datetime.now(timezone.utc)
    if session.status != "pending" or now > session.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session expired or already used",
        )

    # Look up master by tg_user_id
    master_result = await db.execute(
        select(Master).where(
            Master.tg_user_id == data.tg_user_id,
            Master.is_active.is_(True),
        )
    )
    master = master_result.scalar_one_or_none()
    if master is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master account not found for this Telegram user",
        )

    # Create JWT and confirm session
    jwt_token = create_access_token(data={"sub": str(master.id)})
    session.access_token = jwt_token
    session.status = "confirmed"
    session.master_id = master.id
    await db.flush()

    return {"ok": True}


# --- Magic Link Login Flow ---


@router.post("/bot-register", response_model=TokenResponse, status_code=201)
async def bot_register(
    data: BotRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Register a new master from a bot interaction (no password required).

    Creates a Master with name, email, and the platform_user_id column
    set based on the platform field.
    """
    master, token = await register_master_from_bot(
        db, data.name, data.email, data.platform, data.platform_user_id
    )
    return TokenResponse(access_token=token)


@router.post("/link-account", response_model=TokenResponse)
async def link_account(
    data: LinkAccountRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Link an existing master account to a messenger platform.

    Looks up the master by email, sets the platform_user_id column,
    and returns a JWT for the linked master.
    """
    email_lower = data.email.lower().strip()

    # Look up master by email
    result = await db.execute(
        select(Master).where(Master.email == email_lower)
    )
    master = result.scalar_one_or_none()
    if master is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    if not master.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Determine which column to set
    column_name = PLATFORM_COLUMN_MAP.get(data.platform)
    if not column_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported platform: {data.platform}",
        )

    current_value = getattr(master, column_name)

    # Already linked to this same user -- just return a token
    if current_value == data.platform_user_id:
        token = create_access_token(data={"sub": str(master.id)})
        return TokenResponse(access_token=token)

    # Already linked to a DIFFERENT user
    if current_value is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account already linked to a different platform user",
        )

    # Check that platform_user_id is not used by another master
    column = getattr(Master, column_name)
    existing = await db.execute(
        select(Master).where(column == data.platform_user_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Platform account already linked to another master",
        )

    # Link the platform
    setattr(master, column_name, data.platform_user_id)
    await db.flush()

    token = create_access_token(data={"sub": str(master.id)})
    return TokenResponse(access_token=token)


@router.post("/magic/verify", response_model=TokenResponse)
async def magic_link_verify(
    data: MagicLinkVerifyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Verify a magic link token and return a JWT. No auth required.

    Called when user clicks the magic link sent by the bot.
    Validates token exists, not expired, not used.
    """
    result = await db.execute(
        select(QrSession).where(
            QrSession.token == data.token,
            QrSession.session_type == "magic_link",
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid magic link",
        )

    now = datetime.now(timezone.utc)
    if session.status != "pending" or now > session.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Magic link expired or already used",
        )

    if session.master_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid magic link",
        )

    # Look up master
    master_result = await db.execute(
        select(Master).where(
            Master.id == session.master_id,
            Master.is_active.is_(True),
        )
    )
    master = master_result.scalar_one_or_none()
    if master is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master account not found",
        )

    # Create JWT and mark session as used
    jwt_token = create_access_token(data={"sub": str(master.id)})
    session.status = "used"
    await db.flush()

    return TokenResponse(access_token=jwt_token)
