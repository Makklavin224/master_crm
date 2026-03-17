"""Handler for /link command -- generate shareable booking deep link."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.master import Master

logger = logging.getLogger(__name__)

router = Router(name="link")


@router.message(Command("link"))
async def cmd_link(message: Message, db: AsyncSession) -> None:
    """Send the master their shareable booking deep link."""
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

    # Get bot username for the deep link
    bot_info = await message.bot.get_me()
    bot_username = bot_info.username

    link = f"https://t.me/{bot_username}?start={master.id}"
    await message.answer(
        f"\u0412\u0430\u0448\u0430 \u0441\u0441\u044b\u043b\u043a\u0430 "
        f"\u0434\u043b\u044f \u0437\u0430\u043f\u0438\u0441\u0438:\n\n"
        f"{link}\n\n"
        f"\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 "
        f"\u0435\u0451 \u043a\u043b\u0438\u0435\u043d\u0442\u0430\u043c "
        f"\u2014 \u043e\u043d\u0438 \u0441\u043c\u043e\u0433\u0443\u0442 "
        f"\u0437\u0430\u043f\u0438\u0441\u0430\u0442\u044c\u0441\u044f "
        f"\u0447\u0435\u0440\u0435\u0437 "
        f"\u043c\u0438\u043d\u0438-\u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0435.",
        parse_mode="HTML",
    )
