"""Handler for /start command.

Three paths:
- /start (no args): Master registration or welcome back
- /start qr_{session_id} (QR deep link): Confirm QR login session
- /start MASTER_ID (deep link): Client booking entry point
"""

import logging
import uuid
from datetime import datetime, timezone

from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token
from app.models.master import Master
from app.models.qr_session import QrSession

logger = logging.getLogger(__name__)

router = Router(name="start")


@router.message(CommandStart(deep_link=False))
async def start_no_link(message: Message, db: AsyncSession) -> None:
    """Master /start -- register new account or show welcome back."""
    tg_user_id = str(message.from_user.id)

    # Check if master already registered
    result = await db.execute(
        select(Master).where(Master.tg_user_id == tg_user_id)
    )
    master = result.scalar_one_or_none()

    if master:
        # Welcome back with management options
        keyboard = _master_keyboard()
        await message.answer(
            f"<b>\u0421 \u0432\u043e\u0437\u0432\u0440\u0430\u0449\u0435\u043d\u0438\u0435\u043c, "
            f"{master.name}!</b>\n\n"
            "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435:",
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    else:
        # Create new master
        name = message.from_user.full_name or "Master"
        master = Master(
            name=name,
            tg_user_id=tg_user_id,
        )
        db.add(master)
        await db.flush()

        keyboard = _panel_keyboard()
        await message.answer(
            "<b>\u0414\u043e\u0431\u0440\u043e "
            "\u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c "
            "\u0432 \u041c\u0430\u0441\u0442\u0435\u0440-CRM!</b>\n\n"
            "\u0412\u0430\u0448 \u0430\u043a\u043a\u0430\u0443\u043d\u0442 "
            "\u0441\u043e\u0437\u0434\u0430\u043d.\n\n"
            "\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u0442\u0435 "
            "\u0443\u0441\u043b\u0443\u0433\u0438 \u0438 "
            "\u0440\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435, "
            "\u0447\u0442\u043e\u0431\u044b \u043a\u043b\u0438\u0435\u043d\u0442\u044b "
            "\u043c\u043e\u0433\u043b\u0438 "
            "\u0437\u0430\u043f\u0438\u0441\u044b\u0432\u0430\u0442\u044c\u0441\u044f.",
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        logger.info(
            "New master registered via TG: %s (tg_user_id=%s)",
            master.id,
            tg_user_id,
        )


@router.message(CommandStart(deep_link=True))
async def start_with_deep_link(
    message: Message, command: CommandObject, db: AsyncSession
) -> None:
    """Handle deep links: /start qr_{session_id} or /start MASTER_ID."""
    args = command.args
    if not args:
        await message.answer(
            "\u041c\u0430\u0441\u0442\u0435\u0440 \u043d\u0435 "
            "\u043d\u0430\u0439\u0434\u0435\u043d. "
            "\u041f\u0440\u043e\u0432\u0435\u0440\u044c\u0442\u0435 "
            "\u0441\u0441\u044b\u043b\u043a\u0443."
        )
        return

    # --- QR Code Login Deep Link ---
    if args.startswith("qr_"):
        await _handle_qr_login(message, args[3:], db)
        return

    # --- Client Booking Deep Link ---
    # Validate UUID format
    try:
        master_id = uuid.UUID(args)
    except ValueError:
        await message.answer(
            "\u041c\u0430\u0441\u0442\u0435\u0440 \u043d\u0435 "
            "\u043d\u0430\u0439\u0434\u0435\u043d. "
            "\u041f\u0440\u043e\u0432\u0435\u0440\u044c\u0442\u0435 "
            "\u0441\u0441\u044b\u043b\u043a\u0443."
        )
        return

    # Verify master exists and is active
    result = await db.execute(
        select(Master).where(
            Master.id == master_id, Master.is_active.is_(True)
        )
    )
    master = result.scalar_one_or_none()
    if not master:
        await message.answer(
            "\u041c\u0430\u0441\u0442\u0435\u0440 \u043d\u0435 "
            "\u043d\u0430\u0439\u0434\u0435\u043d. "
            "\u041f\u0440\u043e\u0432\u0435\u0440\u044c\u0442\u0435 "
            "\u0441\u0441\u044b\u043b\u043a\u0443."
        )
        return

    # Show booking mini-app button
    mini_app_url = f"{settings.mini_app_url}?master={master_id}"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\U0001f4c5 \u0417\u0430\u043f\u0438\u0441\u0430\u0442\u044c\u0441\u044f",
                    web_app=WebAppInfo(url=mini_app_url),
                )
            ]
        ]
    )
    await message.answer(
        f"\u041e\u0442\u043a\u0440\u043e\u0439\u0442\u0435 "
        f"\u043c\u0438\u043d\u0438-\u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0435 "
        f"\u0434\u043b\u044f \u0437\u0430\u043f\u0438\u0441\u0438 "
        f"\u043a <b>{master.name}</b>:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def _handle_qr_login(
    message: Message, session_id_str: str, db: AsyncSession
) -> None:
    """Confirm a QR login session (called from /start qr_{session_id} deep link)."""
    tg_user_id = str(message.from_user.id)

    # Validate session UUID
    try:
        sid = uuid.UUID(session_id_str)
    except ValueError:
        await message.answer(
            "\u041d\u0435\u0432\u0435\u0440\u043d\u044b\u0439 QR-\u043a\u043e\u0434. "
            "\u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u0435\u0449\u0451 \u0440\u0430\u0437."
        )
        return

    # Look up QR session
    result = await db.execute(
        select(QrSession).where(QrSession.id == sid)
    )
    session = result.scalar_one_or_none()
    if session is None:
        await message.answer(
            "QR-\u0441\u0435\u0441\u0441\u0438\u044f \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430."
        )
        return

    # Check session validity
    now = datetime.now(timezone.utc)
    if session.status != "pending" or now > session.expires_at:
        await message.answer(
            "QR-\u043a\u043e\u0434 \u0438\u0441\u0442\u0451\u043a. "
            "\u0421\u0433\u0435\u043d\u0435\u0440\u0438\u0440\u0443\u0439\u0442\u0435 \u043d\u043e\u0432\u044b\u0439 "
            "\u0432 \u043f\u0430\u043d\u0435\u043b\u0438 \u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u044f."
        )
        return

    # Look up master by tg_user_id
    master_result = await db.execute(
        select(Master).where(
            Master.tg_user_id == tg_user_id,
            Master.is_active.is_(True),
        )
    )
    master = master_result.scalar_one_or_none()
    if master is None:
        await message.answer(
            "\u0410\u043a\u043a\u0430\u0443\u043d\u0442 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d. "
            "\u0421\u043d\u0430\u0447\u0430\u043b\u0430 "
            "\u043e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /start "
            "\u0434\u043b\u044f \u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u0438."
        )
        return

    # Create JWT and confirm session
    jwt_token = create_access_token(data={"sub": str(master.id)})
    session.access_token = jwt_token
    session.status = "confirmed"
    session.master_id = master.id
    await db.flush()

    await message.answer(
        "\u2705 \u0412\u0445\u043e\u0434 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0451\u043d! "
        "\u0412\u0435\u0440\u043d\u0438\u0442\u0435\u0441\u044c "
        "\u0432 \u043f\u0430\u043d\u0435\u043b\u044c \u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u044f."
    )
    logger.info(
        "QR login confirmed: master=%s, session=%s",
        master.id,
        session_id_str,
    )


def _master_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for master welcome back."""
    buttons = [
        [
            InlineKeyboardButton(
                text="\U0001f4c5 \u0417\u0430\u043f\u0438\u0441\u0438 "
                     "\u043d\u0430 \u0441\u0435\u0433\u043e\u0434\u043d\u044f",
                callback_data="today",
            ),
            InlineKeyboardButton(
                text="\U0001f517 \u041c\u043e\u044f \u0441\u0441\u044b\u043b\u043a\u0430",
                callback_data="link",
            ),
        ],
    ]
    if settings.mini_app_url:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="\U0001f4f1 \u041e\u0442\u043a\u0440\u044b\u0442\u044c "
                         "\u043f\u0430\u043d\u0435\u043b\u044c",
                    web_app=WebAppInfo(url=settings.mini_app_url),
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _panel_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard with panel link for new master."""
    buttons = []
    if settings.mini_app_url:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="\U0001f4f1 \u041e\u0442\u043a\u0440\u044b\u0442\u044c "
                         "\u043f\u0430\u043d\u0435\u043b\u044c",
                    web_app=WebAppInfo(url=settings.mini_app_url),
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)
