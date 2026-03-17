"""Handler for /settings command -- management panel links."""

import logging

from aiogram import Router
from aiogram.filters import Command
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

router = Router(name="settings")


@router.message(Command("settings"))
async def cmd_settings(message: Message, db: AsyncSession) -> None:
    """Show management panel links via inline keyboard."""
    tg_user_id = str(message.from_user.id)

    result = await db.execute(
        select(Master).where(Master.tg_user_id == tg_user_id)
    )
    master = result.scalar_one_or_none()
    if not master:
        await message.answer(
            "\u0412\u044b \u043d\u0435 "
            "\u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d\u044b. "
            "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /start"
        )
        return

    base = settings.mini_app_url
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\U0001f487 \u0423\u0441\u043b\u0443\u0433\u0438",
                    web_app=WebAppInfo(url=f"{base}/master/services"),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\U0001f4c5 \u0420\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435",
                    web_app=WebAppInfo(url=f"{base}/master/schedule"),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\u2699\ufe0f \u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438",
                    web_app=WebAppInfo(url=f"{base}/master/settings"),
                ),
            ],
        ]
    )
    await message.answer(
        "<b>\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435</b>\n\n"
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0440\u0430\u0437\u0434\u0435\u043b:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
