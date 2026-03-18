"""Handlers for inline keyboard callback queries.

Handles: today (schedule view), booking:{id} (detail), cancel:{id} (cancel),
and link (generate booking link).
"""

import logging
import uuid

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking
from app.models.client import ClientPlatform
from app.models.master import Master
from app.services.booking_service import cancel_booking

from fastapi import HTTPException

logger = logging.getLogger(__name__)

router = Router(name="callbacks")


@router.callback_query(F.data == "today")
async def cb_today(callback: CallbackQuery, db: AsyncSession) -> None:
    """Show today's bookings (same as /today but edits message)."""
    await callback.answer()

    tg_user_id = str(callback.from_user.id)
    result = await db.execute(
        select(Master).where(Master.tg_user_id == tg_user_id)
    )
    master = result.scalar_one_or_none()
    if not master:
        await callback.message.edit_text(
            "\u0412\u044b \u043d\u0435 "
            "\u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d\u044b. "
            "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /start"
        )
        return

    from app.bots.telegram.handlers.today import format_today_bookings

    text, keyboard = await format_today_bookings(db, master)
    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=keyboard
    )


@router.callback_query(F.data == "link")
async def cb_link(callback: CallbackQuery, db: AsyncSession) -> None:
    """Generate and show the master's booking link."""
    await callback.answer()

    tg_user_id = str(callback.from_user.id)
    result = await db.execute(
        select(Master).where(Master.tg_user_id == tg_user_id)
    )
    master = result.scalar_one_or_none()
    if not master:
        await callback.message.edit_text(
            "\u0412\u044b \u043d\u0435 "
            "\u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d\u044b. "
            "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /start"
        )
        return

    bot_info = await callback.bot.get_me()
    bot_username = bot_info.username
    link = f"https://t.me/{bot_username}?start={master.id}"

    await callback.message.edit_text(
        f"\u0412\u0430\u0448\u0430 \u0441\u0441\u044b\u043b\u043a\u0430 "
        f"\u0434\u043b\u044f \u0437\u0430\u043f\u0438\u0441\u0438:\n\n"
        f"{link}\n\n"
        f"\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 "
        f"\u0435\u0451 \u043a\u043b\u0438\u0435\u043d\u0442\u0430\u043c.",
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("booking:"))
async def cb_booking_detail(
    callback: CallbackQuery, db: AsyncSession
) -> None:
    """Show booking detail with cancel option."""
    await callback.answer()

    booking_id_str = callback.data.split(":", 1)[1]
    try:
        booking_id = uuid.UUID(booking_id_str)
    except ValueError:
        await callback.message.edit_text(
            "\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0435 "
            "\u043d\u0430\u0439\u0434\u0435\u043d\u0430."
        )
        return

    result = await db.execute(
        select(Booking)
        .where(Booking.id == booking_id)
        .options(selectinload(Booking.client), selectinload(Booking.service))
    )
    booking = result.scalar_one_or_none()
    if not booking:
        await callback.message.edit_text(
            "\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0435 "
            "\u043d\u0430\u0439\u0434\u0435\u043d\u0430."
        )
        return

    # Format booking details
    from zoneinfo import ZoneInfo

    # Look up master for timezone
    master_result = await db.execute(
        select(Master).where(Master.id == booking.master_id)
    )
    master = master_result.scalar_one_or_none()
    tz = ZoneInfo(master.timezone) if master else ZoneInfo("Europe/Moscow")

    local_start = booking.starts_at.astimezone(tz)
    date_str = local_start.strftime("%d.%m.%Y")
    time_str = local_start.strftime("%H:%M")
    client_name = booking.client.name if booking.client else "\u2014"
    service_name = booking.service.name if booking.service else "\u2014"
    price_str = ""
    if booking.service and booking.service.price:
        price_str = f"\n\U0001f4b0 {booking.service.price // 100} \u20bd"

    status_map = {
        "confirmed": "\u2705 \u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0430",
        "pending": "\u23f3 \u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435",
        "completed": "\u2705 \u0417\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0430",
        "cancelled_by_client": "\u274c \u041e\u0442\u043c\u0435\u043d\u0435\u043d\u0430 \u043a\u043b\u0438\u0435\u043d\u0442\u043e\u043c",
        "cancelled_by_master": "\u274c \u041e\u0442\u043c\u0435\u043d\u0435\u043d\u0430",
        "no_show": "\u2753 \u041d\u0435\u044f\u0432\u043a\u0430",
    }
    status_text = status_map.get(booking.status, booking.status)

    text = (
        f"<b>\u0417\u0430\u043f\u0438\u0441\u044c "
        f"#{str(booking.id)[:8]}</b>\n\n"
        f"\U0001f464 {client_name}\n"
        f"\U0001f487 {service_name}\n"
        f"\U0001f4c5 {date_str}\n"
        f"\U0001f550 {time_str}"
        f"{price_str}\n\n"
        f"\u0421\u0442\u0430\u0442\u0443\u0441: {status_text}"
    )

    # Action buttons
    buttons = []
    if booking.status in ("confirmed", "pending"):
        buttons.append(
            [
                InlineKeyboardButton(
                    text="\u274c \u041e\u0442\u043c\u0435\u043d\u0438\u0442\u044c",
                    callback_data=f"cancel:{booking.id}",
                ),
                InlineKeyboardButton(
                    text="\U0001f4c5 \u041d\u0430\u0437\u0430\u0434 "
                         "\u043a \u0437\u0430\u043f\u0438\u0441\u044f\u043c",
                    callback_data="today",
                ),
            ]
        )
    else:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="\U0001f4c5 \u041d\u0430\u0437\u0430\u0434 "
                         "\u043a \u0437\u0430\u043f\u0438\u0441\u044f\u043c",
                    callback_data="today",
                ),
            ]
        )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("cancel:"))
async def cb_cancel_booking(
    callback: CallbackQuery, db: AsyncSession
) -> None:
    """Cancel a booking by master (no deadline restriction)."""
    await callback.answer()

    booking_id_str = callback.data.split(":", 1)[1]
    try:
        booking_id = uuid.UUID(booking_id_str)
    except ValueError:
        await callback.message.edit_text(
            "\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0435 "
            "\u043d\u0430\u0439\u0434\u0435\u043d\u0430."
        )
        return

    try:
        booking = await cancel_booking(
            db=db,
            booking_id=booking_id,
            cancelled_by="master",
        )
        await callback.message.edit_text(
            "\u2705 \u0417\u0430\u043f\u0438\u0441\u044c "
            "\u043e\u0442\u043c\u0435\u043d\u0435\u043d\u0430.\n\n"
            "\u041a\u043b\u0438\u0435\u043d\u0442 "
            "\u043f\u043e\u043b\u0443\u0447\u0438\u0442 "
            "\u0443\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u0435.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="\U0001f4c5 \u041a \u0437\u0430\u043f\u0438\u0441\u044f\u043c",
                            callback_data="today",
                        )
                    ]
                ]
            ),
        )
    except Exception:
        logger.exception("Failed to cancel booking %s", booking_id)
        await callback.message.edit_text(
            "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c "
            "\u043e\u0442\u043c\u0435\u043d\u0438\u0442\u044c "
            "\u0437\u0430\u043f\u0438\u0441\u044c.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="\U0001f4c5 \u041d\u0430\u0437\u0430\u0434",
                            callback_data="today",
                        )
                    ]
                ]
            ),
        )


@router.callback_query(F.data.startswith("cancel_client:"))
async def cb_cancel_client(
    callback: CallbackQuery, db: AsyncSession
) -> None:
    """Cancel a booking by client (with deadline enforcement).

    Security: verifies that the callback sender matches the booking's
    client's telegram platform_user_id.
    """
    await callback.answer()

    booking_id_str = callback.data.split(":", 1)[1]
    try:
        booking_id = uuid.UUID(booking_id_str)
    except ValueError:
        await callback.message.edit_text(
            "\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0435 "
            "\u043d\u0430\u0439\u0434\u0435\u043d\u0430."
        )
        return

    # Load booking with client
    result = await db.execute(
        select(Booking)
        .where(Booking.id == booking_id)
        .options(
            selectinload(Booking.client),
            selectinload(Booking.service),
        )
    )
    booking = result.scalar_one_or_none()
    if not booking:
        await callback.message.edit_text(
            "\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0435 "
            "\u043d\u0430\u0439\u0434\u0435\u043d\u0430."
        )
        return

    # Security: verify the callback sender is the booking's client
    sender_tg_id = str(callback.from_user.id)
    client_platform_result = await db.execute(
        select(ClientPlatform).where(
            ClientPlatform.client_id == booking.client_id,
            ClientPlatform.platform == "telegram",
        )
    )
    client_platform = client_platform_result.scalar_one_or_none()
    if not client_platform or client_platform.platform_user_id != sender_tg_id:
        await callback.message.edit_text(
            "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c "
            "\u043e\u0442\u043c\u0435\u043d\u0438\u0442\u044c "
            "\u0437\u0430\u043f\u0438\u0441\u044c."
        )
        return

    # Load master for cancellation_deadline_hours
    master_result = await db.execute(
        select(Master).where(Master.id == booking.master_id)
    )
    master = master_result.scalar_one_or_none()
    deadline_hours = master.cancellation_deadline_hours if master else 24

    try:
        await cancel_booking(
            db=db,
            booking_id=booking_id,
            cancelled_by="client",
            cancellation_deadline_hours=deadline_hours,
        )
        await callback.message.edit_text(
            "\u2705 \u0417\u0430\u043f\u0438\u0441\u044c "
            "\u043e\u0442\u043c\u0435\u043d\u0435\u043d\u0430."
        )
    except HTTPException as exc:
        if exc.status_code == 400:
            await callback.message.edit_text(
                "\u041e\u0442\u043c\u0435\u043d\u0430 "
                "\u043d\u0435\u0432\u043e\u0437\u043c\u043e\u0436\u043d\u0430. "
                "\u0421\u0440\u043e\u043a \u043e\u0442\u043c\u0435\u043d\u044b "
                "\u0438\u0441\u0442\u0451\u043a."
            )
        else:
            await callback.message.edit_text(
                "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c "
                "\u043e\u0442\u043c\u0435\u043d\u0438\u0442\u044c "
                "\u0437\u0430\u043f\u0438\u0441\u044c."
            )
    except Exception:
        logger.exception("Failed to cancel booking %s via client callback", booking_id)
        await callback.message.edit_text(
            "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c "
            "\u043e\u0442\u043c\u0435\u043d\u0438\u0442\u044c "
            "\u0437\u0430\u043f\u0438\u0441\u044c."
        )
