"""Handler for /today command -- show today's bookings."""

import logging
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.booking import Booking
from app.models.master import Master

logger = logging.getLogger(__name__)

router = Router(name="today")


@router.message(Command("today"))
async def cmd_today(message: Message, db: AsyncSession) -> None:
    """Show today's bookings for the master."""
    tg_user_id = str(message.from_user.id)

    # Look up master
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

    text, keyboard = await format_today_bookings(db, master)
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


async def format_today_bookings(
    db: AsyncSession, master: Master
) -> tuple[str, InlineKeyboardMarkup]:
    """Format today's bookings as HTML text + keyboard. Reused by callback handler."""
    tz = ZoneInfo(master.timezone)
    now = datetime.now(tz)
    today_start = datetime.combine(now.date(), time.min, tzinfo=tz)
    today_end = today_start + timedelta(days=1)

    # Query today's bookings
    stmt = (
        select(Booking)
        .where(
            and_(
                Booking.master_id == master.id,
                Booking.status.in_(["confirmed", "pending"]),
                Booking.starts_at >= today_start,
                Booking.starts_at < today_end,
            )
        )
        .options(selectinload(Booking.client), selectinload(Booking.service))
        .order_by(Booking.starts_at.asc())
    )
    result = await db.execute(stmt)
    bookings = list(result.scalars().all())

    if not bookings:
        text = (
            "\u0421\u0435\u0433\u043e\u0434\u043d\u044f "
            "\u0437\u0430\u043f\u0438\u0441\u0435\u0439 "
            "\u043d\u0435\u0442. \u041e\u0442\u043b\u0438\u0447\u043d\u044b\u0439 "
            "\u0434\u0435\u043d\u044c, \u0447\u0442\u043e\u0431\u044b "
            "\u043e\u0442\u0434\u043e\u0445\u043d\u0443\u0442\u044c "
            "\u0438\u043b\u0438 \u043f\u0440\u0438\u043d\u044f\u0442\u044c "
            "\u043d\u043e\u0432\u044b\u0445 "
            "\u043a\u043b\u0438\u0435\u043d\u0442\u043e\u0432."
        )
    else:
        date_str = now.strftime("%d.%m.%Y")
        lines = [
            f"<b>\u0417\u0430\u043f\u0438\u0441\u0438 "
            f"\u043d\u0430 {date_str}:</b>\n"
        ]
        for b in bookings:
            local_time = b.starts_at.astimezone(tz).strftime("%H:%M")
            client_name = b.client.name if b.client else "\u2014"
            service_name = b.service.name if b.service else "\u2014"
            lines.append(
                f"\U0001f550 {local_time} \u2014 {client_name}\n"
                f"\U0001f487 {service_name}"
            )
        text = "\n\n".join(lines)

    # Panel button
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
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    return text, keyboard
