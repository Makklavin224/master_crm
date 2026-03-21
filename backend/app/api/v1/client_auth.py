"""Client cabinet OTP authentication endpoints.

POST /request-code  - Send 6-digit OTP via messenger bot
POST /verify-code   - Verify OTP, return session token in httpOnly cookie (7d)
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.bots.common.notification import notification_service
from app.core.dependencies import get_db
from app.models.client import Client, ClientPlatform
from app.models.client_session import ClientSession
from app.schemas.client import OTPRequest, OTPResponse, OTPVerify, SessionResponse
from app.services.phone_service import normalize_phone

logger = logging.getLogger(__name__)

router = APIRouter()

# Constants
OTP_EXPIRY_MINUTES = 5
SESSION_EXPIRY_DAYS = 7
MAX_OTP_ATTEMPTS = 3
COOLDOWN_SECONDS = 60
PLATFORM_PRIORITY = ["telegram", "max", "vk"]


def _hash_code(code: str) -> str:
    """SHA-256 hash of OTP code."""
    return hashlib.sha256(code.encode()).hexdigest()


@router.post("/request-code", response_model=OTPResponse)
async def request_otp_code(
    body: OTPRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OTPResponse:
    """Generate 6-digit OTP, store hashed in client_sessions, send via messenger."""
    # Normalize phone
    phone = normalize_phone(body.phone)
    if not phone:
        raise HTTPException(status_code=422, detail="Некорректный номер телефона")

    # Look up client
    result = await db.execute(
        select(Client).where(Client.phone == phone)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=404,
            detail="Клиент не найден. Сначала запишитесь к мастеру.",
        )

    # Check cooldown: any session created within last 60 seconds for this phone
    now = datetime.now(timezone.utc)
    cooldown_cutoff = now - timedelta(seconds=COOLDOWN_SECONDS)
    result = await db.execute(
        select(ClientSession)
        .where(
            ClientSession.phone == phone,
            ClientSession.created_at > cooldown_cutoff,
        )
        .order_by(ClientSession.created_at.desc())
        .limit(1)
    )
    recent_session = result.scalar_one_or_none()
    if recent_session:
        elapsed = (now - recent_session.created_at).total_seconds()
        remaining = max(1, int(COOLDOWN_SECONDS - elapsed))
        raise HTTPException(
            status_code=429,
            detail=f"Подождите {remaining} сек. перед повторной отправкой",
        )

    # Generate 6-digit code
    code = str(secrets.randbelow(900000) + 100000)
    code_hash = _hash_code(code)

    # Cleanup: delete existing unverified sessions for this phone
    result = await db.execute(
        select(ClientSession).where(
            ClientSession.phone == phone,
            ClientSession.is_verified == False,  # noqa: E712
        )
    )
    old_sessions = result.scalars().all()
    for s in old_sessions:
        await db.delete(s)

    # Create new session with OTP
    session = ClientSession(
        client_id=client.id,
        phone=phone,
        token=secrets.token_urlsafe(64),
        otp_hash=code_hash,
        otp_attempts=0,
        is_verified=False,
        expires_at=now + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )
    db.add(session)
    await db.flush()

    # Send OTP via messenger bot
    result = await db.execute(
        select(ClientPlatform)
        .where(ClientPlatform.client_id == client.id)
        .options(selectinload(ClientPlatform.client))
    )
    platforms = result.scalars().all()

    sent = False
    if platforms:
        # Sort by priority: telegram > max > vk
        platform_map = {p.platform: p for p in platforms}
        for pname in PLATFORM_PRIORITY:
            if pname in platform_map:
                cp = platform_map[pname]
                sent = await notification_service.send_message(
                    platform=cp.platform,
                    platform_user_id=cp.platform_user_id,
                    text=f"Ваш код для входа: {code}",
                )
                if sent:
                    break

    if not sent:
        logger.warning(
            "Could not send OTP to client %s (phone=%s): no platform or delivery failed",
            client.id,
            phone,
        )
        # SMS fallback not yet integrated — return honest error
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Не удалось отправить код. Запишитесь через Telegram, MAX или VK — тогда код придёт в мессенджер.",
        )

    return OTPResponse(success=True, message="Код отправлен")


@router.post("/verify-code", response_model=SessionResponse)
async def verify_otp_code(
    body: OTPVerify,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionResponse:
    """Verify OTP code, activate session, set httpOnly cookie (7 days)."""
    phone = normalize_phone(body.phone)
    if not phone:
        raise HTTPException(status_code=422, detail="Некорректный номер телефона")

    now = datetime.now(timezone.utc)

    # Find the latest unverified, non-expired session for this phone
    result = await db.execute(
        select(ClientSession)
        .where(
            ClientSession.phone == phone,
            ClientSession.is_verified == False,  # noqa: E712
            ClientSession.expires_at > now,
        )
        .order_by(ClientSession.created_at.desc())
        .limit(1)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=400, detail="Код истёк или не запрошен")

    # Check attempts
    if session.otp_attempts >= MAX_OTP_ATTEMPTS:
        await db.delete(session)
        await db.flush()
        raise HTTPException(
            status_code=400,
            detail="Превышено количество попыток. Запросите новый код.",
        )

    # Compare hashes
    submitted_hash = _hash_code(body.code)
    if submitted_hash != session.otp_hash:
        session.otp_attempts += 1
        await db.flush()
        remaining = MAX_OTP_ATTEMPTS - session.otp_attempts
        raise HTTPException(
            status_code=400,
            detail=f"Неверный код. Осталось попыток: {remaining}",
        )

    # Success: verify session, extend to 7 days
    session.is_verified = True
    session.otp_hash = None
    session.otp_attempts = 0
    session.expires_at = now + timedelta(days=SESSION_EXPIRY_DAYS)
    await db.flush()

    # Set httpOnly cookie
    response.set_cookie(
        key="client_session",
        value=session.token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=SESSION_EXPIRY_DAYS * 24 * 3600,
        path="/",
    )

    return SessionResponse(token=session.token)
