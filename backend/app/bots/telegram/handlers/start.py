"""Handler for /start command.

Two paths:
- /start (no args): Master registration or welcome back
- /start MASTER_ID (deep link): Client booking entry point
"""

import logging
import uuid

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
from app.models.master import Master

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
    """Client deep link: /start MASTER_ID -- show booking mini-app button."""
    master_id_str = command.args
    if not master_id_str:
        await message.answer(
            "\u041c\u0430\u0441\u0442\u0435\u0440 \u043d\u0435 "
            "\u043d\u0430\u0439\u0434\u0435\u043d. "
            "\u041f\u0440\u043e\u0432\u0435\u0440\u044c\u0442\u0435 "
            "\u0441\u0441\u044b\u043b\u043a\u0443."
        )
        return

    # Validate UUID format
    try:
        master_id = uuid.UUID(master_id_str)
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
