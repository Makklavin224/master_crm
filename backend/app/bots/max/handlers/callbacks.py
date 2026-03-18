"""Handlers for callback button presses in MAX.

Handles: today (schedule view), booking:{id} (detail), cancel:{id} (master cancel),
cancel_client:{id} (client cancel), link (booking link), my_bookings:{master_id}.
"""

import logging
import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.booking import Booking
from app.models.client import ClientPlatform
from app.models.master import Master
from app.services.booking_service import cancel_booking

from fastapi import HTTPException

logger = logging.getLogger(__name__)

BASE_URL = "https://platform-api.max.ru"


async def handle_callback(
    body: dict, db: AsyncSession, token: str
) -> None:
    """Route callback payload to the correct handler."""
    callback = body.get("callback", {})
    callback_id = callback.get("callback_id", "")
    payload = callback.get("payload", "")
    user = callback.get("user", {})
    max_user_id = str(user.get("user_id", ""))

    if not max_user_id or not payload:
        return

    # Acknowledge the callback
    await _answer_callback(token, callback_id)

    if payload == "today":
        await _cb_today(max_user_id, db, token)
    elif payload == "link":
        await _cb_link(max_user_id, db, token)
    elif payload.startswith("booking:"):
        booking_id_str = payload.split(":", 1)[1]
        await _cb_booking_detail(max_user_id, booking_id_str, db, token)
    elif payload.startswith("cancel:"):
        booking_id_str = payload.split(":", 1)[1]
        await _cb_cancel_booking(max_user_id, booking_id_str, db, token)
    elif payload.startswith("cancel_client:"):
        booking_id_str = payload.split(":", 1)[1]
        await _cb_cancel_client(max_user_id, booking_id_str, db, token)
    elif payload.startswith("my_bookings:"):
        master_id_str = payload.split(":", 1)[1]
        await _cb_my_bookings(max_user_id, master_id_str, token)


async def _answer_callback(token: str, callback_id: str) -> None:
    """Acknowledge a callback to MAX API."""
    if not callback_id:
        return
    headers = {"Authorization": f"access_token={token}"}
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{BASE_URL}/answers",
                params={"callback_id": callback_id},
                headers=headers,
                json={},
                timeout=10.0,
            )
    except Exception:
        logger.exception("Failed to answer MAX callback %s", callback_id)


async def _cb_today(
    max_user_id: str, db: AsyncSession, token: str
) -> None:
    """Show today's bookings."""
    result = await db.execute(
        select(Master).where(Master.max_user_id == max_user_id)
    )
    master = result.scalar_one_or_none()
    if not master:
        await _send(
            token,
            max_user_id,
            "\u0412\u044b \u043d\u0435 \u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d\u044b. "
            "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /start",
        )
        return

    from app.bots.max.handlers.today import format_today_bookings_text

    text = await format_today_bookings_text(db, master)

    buttons: list[list[dict]] = []
    if settings.mini_app_url:
        buttons.append(
            [
                {
                    "type": "open_app",
                    "text": "\U0001f4f1 \u041e\u0442\u043a\u0440\u044b\u0442\u044c \u043f\u0430\u043d\u0435\u043b\u044c",
                    "url": settings.mini_app_url,
                }
            ]
        )

    attachments = None
    if buttons:
        attachments = [
            {
                "type": "inline_keyboard",
                "payload": {"buttons": buttons},
            }
        ]

    await _send(token, max_user_id, text, attachments)


async def _cb_link(
    max_user_id: str, db: AsyncSession, token: str
) -> None:
    """Generate and show the master's MAX booking link."""
    result = await db.execute(
        select(Master).where(Master.max_user_id == max_user_id)
    )
    master = result.scalar_one_or_none()
    if not master:
        await _send(
            token,
            max_user_id,
            "\u0412\u044b \u043d\u0435 \u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d\u044b. "
            "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /start",
        )
        return

    link = f"https://max.ru/{settings.max_bot_username}?startapp={master.id}"
    await _send(
        token,
        max_user_id,
        (
            f"\u0412\u0430\u0448\u0430 \u0441\u0441\u044b\u043b\u043a\u0430 "
            f"\u0434\u043b\u044f \u0437\u0430\u043f\u0438\u0441\u0438:\n\n"
            f"{link}\n\n"
            f"\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 "
            f"\u0435\u0451 \u043a\u043b\u0438\u0435\u043d\u0442\u0430\u043c."
        ),
    )


async def _cb_booking_detail(
    max_user_id: str, booking_id_str: str, db: AsyncSession, token: str
) -> None:
    """Show booking detail with cancel option."""
    try:
        booking_id = uuid.UUID(booking_id_str)
    except ValueError:
        await _send(token, max_user_id, "\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.")
        return

    result = await db.execute(
        select(Booking)
        .where(Booking.id == booking_id)
        .options(selectinload(Booking.client), selectinload(Booking.service))
    )
    booking = result.scalar_one_or_none()
    if not booking:
        await _send(token, max_user_id, "\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.")
        return

    from zoneinfo import ZoneInfo

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

    buttons: list[list[dict]] = []
    if booking.status in ("confirmed", "pending"):
        buttons.append(
            [
                {
                    "type": "callback",
                    "text": "\u274c \u041e\u0442\u043c\u0435\u043d\u0438\u0442\u044c",
                    "payload": f"cancel:{booking.id}",
                },
                {
                    "type": "callback",
                    "text": "\U0001f4c5 \u041d\u0430\u0437\u0430\u0434 \u043a \u0437\u0430\u043f\u0438\u0441\u044f\u043c",
                    "payload": "today",
                },
            ]
        )
    else:
        buttons.append(
            [
                {
                    "type": "callback",
                    "text": "\U0001f4c5 \u041d\u0430\u0437\u0430\u0434 \u043a \u0437\u0430\u043f\u0438\u0441\u044f\u043c",
                    "payload": "today",
                },
            ]
        )

    await _send(
        token,
        max_user_id,
        text,
        [{"type": "inline_keyboard", "payload": {"buttons": buttons}}],
    )


async def _cb_cancel_booking(
    max_user_id: str, booking_id_str: str, db: AsyncSession, token: str
) -> None:
    """Cancel a booking by master (no deadline restriction)."""
    try:
        booking_id = uuid.UUID(booking_id_str)
    except ValueError:
        await _send(token, max_user_id, "\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.")
        return

    try:
        await cancel_booking(
            db=db,
            booking_id=booking_id,
            cancelled_by="master",
        )
        buttons = [
            [
                {
                    "type": "callback",
                    "text": "\U0001f4c5 \u041a \u0437\u0430\u043f\u0438\u0441\u044f\u043c",
                    "payload": "today",
                }
            ]
        ]
        await _send(
            token,
            max_user_id,
            "\u2705 \u0417\u0430\u043f\u0438\u0441\u044c \u043e\u0442\u043c\u0435\u043d\u0435\u043d\u0430.\n\n"
            "\u041a\u043b\u0438\u0435\u043d\u0442 \u043f\u043e\u043b\u0443\u0447\u0438\u0442 \u0443\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u0435.",
            [{"type": "inline_keyboard", "payload": {"buttons": buttons}}],
        )
    except Exception:
        logger.exception("Failed to cancel booking %s via MAX", booking_id)
        buttons = [
            [
                {
                    "type": "callback",
                    "text": "\U0001f4c5 \u041d\u0430\u0437\u0430\u0434",
                    "payload": "today",
                }
            ]
        ]
        await _send(
            token,
            max_user_id,
            "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043e\u0442\u043c\u0435\u043d\u0438\u0442\u044c \u0437\u0430\u043f\u0438\u0441\u044c.",
            [{"type": "inline_keyboard", "payload": {"buttons": buttons}}],
        )


async def _cb_cancel_client(
    max_user_id: str, booking_id_str: str, db: AsyncSession, token: str
) -> None:
    """Cancel a booking by client (with deadline enforcement).

    Security: verifies that the callback sender matches the booking's
    client's MAX platform_user_id.
    """
    try:
        booking_id = uuid.UUID(booking_id_str)
    except ValueError:
        await _send(token, max_user_id, "\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.")
        return

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
        await _send(token, max_user_id, "\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.")
        return

    # Security: verify the callback sender is the booking's client
    client_platform_result = await db.execute(
        select(ClientPlatform).where(
            ClientPlatform.client_id == booking.client_id,
            ClientPlatform.platform == "max",
        )
    )
    client_platform = client_platform_result.scalar_one_or_none()
    if not client_platform or client_platform.platform_user_id != max_user_id:
        await _send(
            token,
            max_user_id,
            "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043e\u0442\u043c\u0435\u043d\u0438\u0442\u044c \u0437\u0430\u043f\u0438\u0441\u044c.",
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
        await _send(
            token,
            max_user_id,
            "\u2705 \u0417\u0430\u043f\u0438\u0441\u044c \u043e\u0442\u043c\u0435\u043d\u0435\u043d\u0430.",
        )
    except HTTPException as exc:
        if exc.status_code == 400:
            await _send(
                token,
                max_user_id,
                "\u041e\u0442\u043c\u0435\u043d\u0430 \u043d\u0435\u0432\u043e\u0437\u043c\u043e\u0436\u043d\u0430. "
                "\u0421\u0440\u043e\u043a \u043e\u0442\u043c\u0435\u043d\u044b \u0438\u0441\u0442\u0451\u043a.",
            )
        else:
            await _send(
                token,
                max_user_id,
                "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043e\u0442\u043c\u0435\u043d\u0438\u0442\u044c \u0437\u0430\u043f\u0438\u0441\u044c.",
            )
    except Exception:
        logger.exception(
            "Failed to cancel booking %s via MAX client callback", booking_id
        )
        await _send(
            token,
            max_user_id,
            "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043e\u0442\u043c\u0435\u043d\u0438\u0442\u044c \u0437\u0430\u043f\u0438\u0441\u044c.",
        )


async def _cb_my_bookings(
    max_user_id: str, master_id_str: str, token: str
) -> None:
    """Show open_app button to view bookings in mini-app."""
    mini_app_url = f"{settings.mini_app_url}?master={master_id_str}"
    buttons = [
        [
            {
                "type": "open_app",
                "text": "\U0001f4cb \u041c\u043e\u0438 \u0437\u0430\u043f\u0438\u0441\u0438",
                "url": mini_app_url,
            }
        ]
    ]
    await _send(
        token,
        max_user_id,
        "\u041e\u0442\u043a\u0440\u043e\u0439\u0442\u0435 \u043c\u0438\u043d\u0438-\u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0435 \u0434\u043b\u044f \u043f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u0430 \u0437\u0430\u043f\u0438\u0441\u0435\u0439:",
        [{"type": "inline_keyboard", "payload": {"buttons": buttons}}],
    )


async def _send(
    token: str,
    chat_id: str,
    text: str,
    attachments: list[dict] | None = None,
) -> None:
    """Send a message via MAX Bot API."""
    headers = {"Authorization": f"access_token={token}"}
    payload: dict = {"text": text, "format": "html"}
    if attachments:
        payload["attachments"] = attachments

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{BASE_URL}/messages",
                params={"chat_id": chat_id},
                headers=headers,
                json=payload,
                timeout=10.0,
            )
    except Exception:
        logger.exception("Failed to send MAX message to %s", chat_id)
