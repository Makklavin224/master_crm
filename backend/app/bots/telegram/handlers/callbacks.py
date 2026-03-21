"""Handlers for inline keyboard callback queries.

Handles: today (schedule view), booking:{id} (detail), cancel:{id} (cancel),
link (generate booking link), register_master, and review_star/review_text/review_done flows.
"""

import logging
import uuid
from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.booking import Booking
from app.models.client import ClientPlatform
from app.models.master import Master
from app.models.review import Review
from app.services.booking_service import cancel_booking

from fastapi import HTTPException

logger = logging.getLogger(__name__)

router = Router(name="callbacks")

# Module-level dict for pending review text input: tg_user_id -> booking_id
_pending_review_text: dict[str, uuid.UUID] = {}

# Module-level dict for pending link-account email input: tg_user_id -> True
_pending_link_email: dict[str, bool] = {}


@router.callback_query(F.data == "register_master")
async def cb_register_master(callback: CallbackQuery, db: AsyncSession) -> None:
    """Explicit master registration -- only creates account when user clicks the button."""
    await callback.answer()

    tg_user_id = str(callback.from_user.id)

    # Check if already registered (race condition guard)
    result = await db.execute(
        select(Master).where(Master.tg_user_id == tg_user_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        await callback.message.edit_text(
            f"\u0412\u044b \u0443\u0436\u0435 "
            f"\u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d\u044b, "
            f"{existing.name}! "
            f"\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /start "
            f"\u0434\u043b\u044f \u0434\u043e\u0441\u0442\u0443\u043f\u0430 "
            f"\u043a \u043f\u0430\u043d\u0435\u043b\u0438."
        )
        return

    # Create new master
    name = callback.from_user.full_name or "Master"
    master = Master(
        name=name,
        tg_user_id=tg_user_id,
    )
    db.add(master)
    await db.flush()

    # Build panel keyboard
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

    await callback.message.edit_text(
        "<b>\u0414\u043e\u0431\u0440\u043e "
        "\u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c "
        "\u0432 \u041c\u043e\u0438\u041e\u043a\u043e\u0448\u043a\u0438!</b>\n\n"
        "\u0412\u0430\u0448 \u0430\u043a\u043a\u0430\u0443\u043d\u0442 "
        "\u0441\u043e\u0437\u0434\u0430\u043d.\n\n"
        "\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u0442\u0435 "
        "\u0443\u0441\u043b\u0443\u0433\u0438 \u0438 "
        "\u0440\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435, "
        "\u0447\u0442\u043e\u0431\u044b \u043a\u043b\u0438\u0435\u043d\u0442\u044b "
        "\u043c\u043e\u0433\u043b\u0438 "
        "\u0437\u0430\u043f\u0438\u0441\u044b\u0432\u0430\u0442\u044c\u0441\u044f.\n\n"
        "\u0420\u0435\u043a\u043e\u043c\u0435\u043d\u0434\u0443\u0435\u043c "
        "\u0434\u043e\u0431\u0430\u0432\u0438\u0442\u044c email "
        "\u0432 \u043d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0430\u0445 "
        "\u0434\u043b\u044f \u0432\u0445\u043e\u0434\u0430 "
        "\u0447\u0435\u0440\u0435\u0437 \u0432\u0435\u0431-\u043f\u0430\u043d\u0435\u043b\u044c.",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    logger.info(
        "New master registered via TG: %s (tg_user_id=%s)",
        master.id,
        tg_user_id,
    )


@router.callback_query(F.data == "link_account")
async def cb_link_account(callback: CallbackQuery, db: AsyncSession) -> None:
    """Start the account linking flow -- ask user to enter their email."""
    await callback.answer()

    tg_user_id = str(callback.from_user.id)

    # Check if already registered (no need to link)
    result = await db.execute(
        select(Master).where(Master.tg_user_id == tg_user_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        await callback.message.edit_text(
            f"\u0412\u0430\u0448 Telegram \u0443\u0436\u0435 \u043f\u0440\u0438\u0432\u044f\u0437\u0430\u043d "
            f"\u043a \u0430\u043a\u043a\u0430\u0443\u043d\u0442\u0443 {existing.name}! "
            f"\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /start "
            f"\u0434\u043b\u044f \u0434\u043e\u0441\u0442\u0443\u043f\u0430 \u043a \u043f\u0430\u043d\u0435\u043b\u0438."
        )
        return

    # Set pending link state
    _pending_link_email[tg_user_id] = True

    await callback.message.edit_text(
        "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 email, "
        "\u043a\u043e\u0442\u043e\u0440\u044b\u0439 \u0432\u044b "
        "\u0443\u043a\u0430\u0437\u0430\u043b\u0438 "
        "\u043f\u0440\u0438 \u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u0438:"
    )


@router.message(F.text, lambda msg: str(msg.from_user.id) in _pending_link_email)
async def msg_link_email(message: Message, db: AsyncSession) -> None:
    """Capture email from user who is in the link-account flow."""
    from app.core.security import create_access_token

    tg_user_id = str(message.from_user.id)
    _pending_link_email.pop(tg_user_id, None)

    email = message.text.strip().lower()

    # Look up master by email
    result = await db.execute(
        select(Master).where(Master.email == email)
    )
    master = result.scalar_one_or_none()

    if master is None:
        await message.answer(
            "\u0410\u043a\u043a\u0430\u0443\u043d\u0442 \u0441 \u0442\u0430\u043a\u0438\u043c email "
            "\u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d. "
            "\u041f\u0440\u043e\u0432\u0435\u0440\u044c\u0442\u0435 email "
            "\u0438\u043b\u0438 \u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u0443\u0439\u0442\u0435\u0441\u044c "
            "\u0437\u0430\u043d\u043e\u0432\u043e \u0447\u0435\u0440\u0435\u0437 /start."
        )
        return

    if master.tg_user_id is not None and master.tg_user_id != tg_user_id:
        await message.answer(
            "\u042d\u0442\u043e\u0442 \u0430\u043a\u043a\u0430\u0443\u043d\u0442 "
            "\u0443\u0436\u0435 \u043f\u0440\u0438\u0432\u044f\u0437\u0430\u043d "
            "\u043a \u0434\u0440\u0443\u0433\u043e\u043c\u0443 Telegram."
        )
        return

    if master.tg_user_id == tg_user_id:
        # Already linked to this user
        keyboard = _build_master_keyboard()
        await message.answer(
            f"\u042d\u0442\u043e\u0442 \u0430\u043a\u043a\u0430\u0443\u043d\u0442 "
            f"\u0443\u0436\u0435 \u043f\u0440\u0438\u0432\u044f\u0437\u0430\u043d "
            f"\u043a \u0432\u0430\u0448\u0435\u043c\u0443 Telegram!",
            reply_markup=keyboard,
        )
        return

    # Link the account
    master.tg_user_id = tg_user_id
    await db.flush()

    keyboard = _build_master_keyboard()
    await message.answer(
        f"\u0410\u043a\u043a\u0430\u0443\u043d\u0442 \u043f\u0440\u0438\u0432\u044f\u0437\u0430\u043d! "
        f"\u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c, "
        f"{master.name}!",
        reply_markup=keyboard,
    )
    logger.info(
        "Account linked via TG: master=%s, tg_user_id=%s",
        master.id,
        tg_user_id,
    )


def _build_master_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for linked/registered master."""
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


# ---- Review flow handlers ----


@router.callback_query(F.data.startswith("review_star:"))
async def cb_review_star(
    callback: CallbackQuery, db: AsyncSession
) -> None:
    """Handle star rating button press from review request."""
    await callback.answer()

    parts = callback.data.split(":")
    if len(parts) != 3:
        return

    booking_id_str = parts[1]
    try:
        booking_id = uuid.UUID(booking_id_str)
        rating = int(parts[2])
    except (ValueError, IndexError):
        return

    if rating < 1 or rating > 5:
        return

    # Security: verify sender is the booking's client
    sender_tg_id = str(callback.from_user.id)
    booking_result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = booking_result.scalar_one_or_none()
    if not booking:
        await callback.message.edit_text(
            "\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430."
        )
        return

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
            "\u043e\u0431\u0440\u0430\u0431\u043e\u0442\u0430\u0442\u044c \u043e\u0446\u0435\u043d\u043a\u0443."
        )
        return

    # Find existing Review row (sentinel from review_request_service)
    review_result = await db.execute(
        select(Review).where(Review.booking_id == booking_id)
    )
    review = review_result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if review and review.rating > 0:
        # Already rated
        await callback.message.edit_text(
            "\u0412\u044b \u0443\u0436\u0435 \u043e\u0441\u0442\u0430\u0432\u0438\u043b\u0438 "
            "\u043e\u0442\u0437\u044b\u0432. \u0421\u043f\u0430\u0441\u0438\u0431\u043e!"
        )
        return

    status = "published" if rating >= 3 else "pending_reply"

    if review:
        # Update sentinel row
        review.rating = rating
        review.status = status
        review.updated_at = now
    else:
        # Create new Review (edge case: no sentinel row)
        review = Review(
            booking_id=booking_id,
            master_id=booking.master_id,
            client_id=booking.client_id,
            rating=rating,
            status=status,
        )
        db.add(review)

    await db.flush()

    # Build star display
    stars = "\u2b50" * rating

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\u0414\u0430, \u043d\u0430\u043f\u0438\u0441\u0430\u0442\u044c",
                    callback_data=f"review_text:{booking_id}",
                ),
                InlineKeyboardButton(
                    text="\u041d\u0435\u0442, \u0441\u043f\u0430\u0441\u0438\u0431\u043e",
                    callback_data=f"review_done:{booking_id}",
                ),
            ]
        ]
    )

    await callback.message.edit_text(
        f"\u0421\u043f\u0430\u0441\u0438\u0431\u043e! \u0412\u0430\u0448\u0430 "
        f"\u043e\u0446\u0435\u043d\u043a\u0430: {stars}\n\n"
        f"\u0425\u043e\u0442\u0438\u0442\u0435 \u0434\u043e\u0431\u0430\u0432\u0438\u0442\u044c "
        f"\u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439?",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("review_text:"))
async def cb_review_text(
    callback: CallbackQuery, db: AsyncSession
) -> None:
    """Handle 'write comment' button -- prompt user for text."""
    await callback.answer()

    booking_id_str = callback.data.split(":", 1)[1]
    try:
        booking_id = uuid.UUID(booking_id_str)
    except ValueError:
        return

    # Store pending text state
    _pending_review_text[str(callback.from_user.id)] = booking_id

    await callback.message.edit_text(
        "\u041d\u0430\u043f\u0438\u0448\u0438\u0442\u0435 \u0432\u0430\u0448 "
        "\u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439 "
        "(\u0434\u043e 500 \u0441\u0438\u043c\u0432\u043e\u043b\u043e\u0432):"
    )


@router.callback_query(F.data.startswith("review_done:"))
async def cb_review_done(
    callback: CallbackQuery, db: AsyncSession
) -> None:
    """Handle 'no thanks' button -- confirm review submission."""
    await callback.answer()

    # Clean up pending state if exists
    _pending_review_text.pop(str(callback.from_user.id), None)

    await callback.message.edit_text(
        "\u0421\u043f\u0430\u0441\u0438\u0431\u043e \u0437\u0430 \u043e\u0442\u0437\u044b\u0432! \U0001f64f"
    )


@router.message(F.text, lambda msg: str(msg.from_user.id) in _pending_review_text)
async def msg_review_text(message: Message, db: AsyncSession) -> None:
    """Capture review text from user who is in pending review text state."""
    tg_user_id = str(message.from_user.id)
    booking_id = _pending_review_text.pop(tg_user_id, None)
    if not booking_id:
        return

    # Update Review with text
    review_result = await db.execute(
        select(Review).where(Review.booking_id == booking_id)
    )
    review = review_result.scalar_one_or_none()
    if review:
        review.text = message.text[:500]
        review.updated_at = datetime.now(timezone.utc)
        await db.flush()

    await message.answer(
        "\u0421\u043f\u0430\u0441\u0438\u0431\u043e \u0437\u0430 \u043e\u0442\u0437\u044b\u0432! \U0001f64f"
    )
