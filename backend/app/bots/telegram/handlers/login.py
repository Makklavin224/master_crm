"""Handler for /login command.

Generates a magic link for web admin panel login.
Creates a QrSession (type='magic_link') and sends an inline keyboard
button with the login URL.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.master import Master
from app.models.qr_session import QrSession

logger = logging.getLogger(__name__)

router = Router(name="login")


@router.message(Command("login"))
async def login_command(message: Message, db: AsyncSession) -> None:
    """Generate a magic link for web admin panel login."""
    tg_user_id = str(message.from_user.id)

    # Look up master by tg_user_id
    result = await db.execute(
        select(Master).where(
            Master.tg_user_id == tg_user_id,
            Master.is_active.is_(True),
        )
    )
    master = result.scalar_one_or_none()
    if master is None:
        await message.answer(
            "\u0410\u043a\u043a\u0430\u0443\u043d\u0442 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d. "
            "\u0421\u043d\u0430\u0447\u0430\u043b\u0430 "
            "\u043e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /start "
            "\u0434\u043b\u044f \u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u0438."
        )
        return

    # Create magic link session
    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    session = QrSession(
        id=uuid.uuid4(),
        session_type="magic_link",
        master_id=master.id,
        token=token,
        status="pending",
        expires_at=expires_at,
    )
    db.add(session)
    await db.flush()

    # Build login URL
    admin_url = settings.web_admin_url.rstrip("/")
    login_url = f"{admin_url}/auth/magic?token={token}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\U0001f510 \u0412\u043e\u0439\u0442\u0438 "
                         "\u0432 \u043f\u0430\u043d\u0435\u043b\u044c",
                    url=login_url,
                )
            ]
        ]
    )
    await message.answer(
        "\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u043a\u043d\u043e\u043f\u043a\u0443, "
        "\u0447\u0442\u043e\u0431\u044b \u0432\u043e\u0439\u0442\u0438 "
        "\u0432 \u043f\u0430\u043d\u0435\u043b\u044c \u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u044f.\n\n"
        "\u0421\u0441\u044b\u043b\u043a\u0430 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0442\u0435\u043b\u044c\u043d\u0430 10 \u043c\u0438\u043d\u0443\u0442.",
        reply_markup=keyboard,
    )
    logger.info(
        "Magic link generated: master=%s, token=%s",
        master.id,
        token[:8] + "...",
    )
