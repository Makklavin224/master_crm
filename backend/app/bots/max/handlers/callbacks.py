"""Handlers for callback button presses in MAX.

Handles: today (schedule view), booking:{id} (detail), cancel:{id} (master cancel),
cancel_client:{id} (client cancel), link (booking link), my_bookings:{master_id},
and review_star/review_text/review_done flows.
"""

import logging
import uuid
from datetime import datetime, timezone

import httpx
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

BASE_URL = "https://platform-api.max.ru"

# Module-level dict for pending review text input: max_user_id -> booking_id
_pending_review_text: dict[str, uuid.UUID] = {}

# Module-level dict for pending link-account email input: max_user_id -> True
_pending_link_email: dict[str, bool] = {}


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

    if payload == "register_master":
        await _cb_register_master(max_user_id, user.get("name", "Master"), db, token)
    elif payload == "link_account":
        await _cb_link_account(max_user_id, db, token)
    elif payload == "today":
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
    elif payload.startswith("review_star:"):
        await _cb_review_star(max_user_id, payload, db, token)
    elif payload.startswith("review_text:"):
        booking_id_str = payload.split(":", 1)[1]
        await _cb_review_text(max_user_id, booking_id_str, token)
    elif payload.startswith("review_done:"):
        await _cb_review_done(max_user_id, token)


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


async def _cb_register_master(
    max_user_id: str, user_name: str, db: AsyncSession, token: str
) -> None:
    """Explicit master registration -- only creates account when user clicks the button."""
    # Check if already registered (race condition guard)
    result = await db.execute(
        select(Master).where(Master.max_user_id == max_user_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        await _send(
            token,
            max_user_id,
            f"\u0412\u044b \u0443\u0436\u0435 "
            f"\u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d\u044b, "
            f"{existing.name}! "
            f"\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /start "
            f"\u0434\u043b\u044f \u0434\u043e\u0441\u0442\u0443\u043f\u0430 "
            f"\u043a \u043f\u0430\u043d\u0435\u043b\u0438.",
        )
        return

    # Create new master
    master = Master(
        name=user_name,
        max_user_id=max_user_id,
    )
    db.add(master)
    await db.flush()

    # Build panel keyboard
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

    attachments = (
        [{"type": "inline_keyboard", "payload": {"buttons": buttons}}]
        if buttons
        else None
    )

    await _send(
        token,
        max_user_id,
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
        attachments=attachments,
    )
    logger.info(
        "New master registered via MAX: %s (max_user_id=%s)",
        master.id,
        max_user_id,
    )


async def _cb_link_account(
    max_user_id: str, db: AsyncSession, token: str
) -> None:
    """Start the account linking flow -- ask user to enter their email."""
    # Check if already registered (no need to link)
    result = await db.execute(
        select(Master).where(Master.max_user_id == max_user_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        await _send(
            token,
            max_user_id,
            f"\u0412\u0430\u0448 MAX \u0443\u0436\u0435 \u043f\u0440\u0438\u0432\u044f\u0437\u0430\u043d "
            f"\u043a \u0430\u043a\u043a\u0430\u0443\u043d\u0442\u0443 {existing.name}! "
            f"\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /start "
            f"\u0434\u043b\u044f \u0434\u043e\u0441\u0442\u0443\u043f\u0430 \u043a \u043f\u0430\u043d\u0435\u043b\u0438.",
        )
        return

    _pending_link_email[max_user_id] = True
    await _send(
        token,
        max_user_id,
        "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 email, "
        "\u043a\u043e\u0442\u043e\u0440\u044b\u0439 \u0432\u044b "
        "\u0443\u043a\u0430\u0437\u0430\u043b\u0438 "
        "\u043f\u0440\u0438 \u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u0438:",
    )


async def handle_link_email_message(
    max_user_id: str, text: str, db: AsyncSession, token: str
) -> bool:
    """Handle incoming text message if user is in pending link-email state.

    Returns True if the message was handled, False otherwise.
    """
    if max_user_id not in _pending_link_email:
        return False

    _pending_link_email.pop(max_user_id, None)

    email = text.strip().lower()

    # Look up master by email
    result = await db.execute(
        select(Master).where(Master.email == email)
    )
    master = result.scalar_one_or_none()

    if master is None:
        await _send(
            token,
            max_user_id,
            "\u0410\u043a\u043a\u0430\u0443\u043d\u0442 \u0441 \u0442\u0430\u043a\u0438\u043c email "
            "\u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d. "
            "\u041f\u0440\u043e\u0432\u0435\u0440\u044c\u0442\u0435 email "
            "\u0438\u043b\u0438 \u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u0443\u0439\u0442\u0435\u0441\u044c "
            "\u0437\u0430\u043d\u043e\u0432\u043e \u0447\u0435\u0440\u0435\u0437 /start.",
        )
        return True

    if master.max_user_id is not None and master.max_user_id != max_user_id:
        await _send(
            token,
            max_user_id,
            "\u042d\u0442\u043e\u0442 \u0430\u043a\u043a\u0430\u0443\u043d\u0442 "
            "\u0443\u0436\u0435 \u043f\u0440\u0438\u0432\u044f\u0437\u0430\u043d "
            "\u043a \u0434\u0440\u0443\u0433\u043e\u043c\u0443 MAX.",
        )
        return True

    if master.max_user_id == max_user_id:
        # Already linked to this user
        buttons = _master_buttons_for_linked()
        await _send(
            token,
            max_user_id,
            "\u042d\u0442\u043e\u0442 \u0430\u043a\u043a\u0430\u0443\u043d\u0442 "
            "\u0443\u0436\u0435 \u043f\u0440\u0438\u0432\u044f\u0437\u0430\u043d "
            "\u043a \u0432\u0430\u0448\u0435\u043c\u0443 MAX!",
            [{"type": "inline_keyboard", "payload": {"buttons": buttons}}],
        )
        return True

    # Link the account
    master.max_user_id = max_user_id
    await db.flush()

    buttons = _master_buttons_for_linked()
    await _send(
        token,
        max_user_id,
        f"\u0410\u043a\u043a\u0430\u0443\u043d\u0442 \u043f\u0440\u0438\u0432\u044f\u0437\u0430\u043d! "
        f"\u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c, "
        f"{master.name}!",
        [{"type": "inline_keyboard", "payload": {"buttons": buttons}}],
    )
    logger.info(
        "Account linked via MAX: master=%s, max_user_id=%s",
        master.id,
        max_user_id,
    )
    return True


def _master_buttons_for_linked() -> list[list[dict]]:
    """Build inline keyboard buttons for a linked/registered master."""
    buttons: list[list[dict]] = [
        [
            {
                "type": "callback",
                "text": "\U0001f4c5 \u0417\u0430\u043f\u0438\u0441\u0438 \u043d\u0430 \u0441\u0435\u0433\u043e\u0434\u043d\u044f",
                "payload": "today",
            },
            {
                "type": "callback",
                "text": "\U0001f517 \u041c\u043e\u044f \u0441\u0441\u044b\u043b\u043a\u0430",
                "payload": "link",
            },
        ],
    ]
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
    return buttons


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


async def _cb_review_star(
    max_user_id: str, payload: str, db: AsyncSession, token: str
) -> None:
    """Handle star rating callback from review request."""
    parts = payload.split(":")
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
    booking_result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = booking_result.scalar_one_or_none()
    if not booking:
        await _send(token, max_user_id, "\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.")
        return

    client_platform_result = await db.execute(
        select(ClientPlatform).where(
            ClientPlatform.client_id == booking.client_id,
            ClientPlatform.platform == "max",
        )
    )
    client_platform = client_platform_result.scalar_one_or_none()
    if not client_platform or client_platform.platform_user_id != max_user_id:
        await _send(
            token, max_user_id,
            "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u0430\u0442\u044c \u043e\u0446\u0435\u043d\u043a\u0443.",
        )
        return

    # Find existing Review row
    review_result = await db.execute(
        select(Review).where(Review.booking_id == booking_id)
    )
    review = review_result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if review and review.rating > 0:
        await _send(
            token, max_user_id,
            "\u0412\u044b \u0443\u0436\u0435 \u043e\u0441\u0442\u0430\u0432\u0438\u043b\u0438 \u043e\u0442\u0437\u044b\u0432. \u0421\u043f\u0430\u0441\u0438\u0431\u043e!",
        )
        return

    status = "published" if rating >= 3 else "pending_reply"

    if review:
        review.rating = rating
        review.status = status
        review.updated_at = now
    else:
        review = Review(
            booking_id=booking_id,
            master_id=booking.master_id,
            client_id=booking.client_id,
            rating=rating,
            status=status,
        )
        db.add(review)

    await db.flush()

    stars = "\u2b50" * rating
    buttons = [
        [
            {
                "type": "callback",
                "text": "\u0414\u0430, \u043d\u0430\u043f\u0438\u0441\u0430\u0442\u044c",
                "payload": f"review_text:{booking_id}",
            },
            {
                "type": "callback",
                "text": "\u041d\u0435\u0442, \u0441\u043f\u0430\u0441\u0438\u0431\u043e",
                "payload": f"review_done:{booking_id}",
            },
        ]
    ]
    await _send(
        token,
        max_user_id,
        f"\u0421\u043f\u0430\u0441\u0438\u0431\u043e! \u0412\u0430\u0448\u0430 \u043e\u0446\u0435\u043d\u043a\u0430: {stars}\n\n"
        f"\u0425\u043e\u0442\u0438\u0442\u0435 \u0434\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439?",
        [{"type": "inline_keyboard", "payload": {"buttons": buttons}}],
    )


async def _cb_review_text(
    max_user_id: str, booking_id_str: str, token: str
) -> None:
    """Handle 'write comment' button -- prompt user for text."""
    try:
        booking_id = uuid.UUID(booking_id_str)
    except ValueError:
        return

    _pending_review_text[max_user_id] = booking_id
    await _send(
        token,
        max_user_id,
        "\u041d\u0430\u043f\u0438\u0448\u0438\u0442\u0435 \u0432\u0430\u0448 \u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439 (\u0434\u043e 500 \u0441\u0438\u043c\u0432\u043e\u043b\u043e\u0432):",
    )


async def _cb_review_done(max_user_id: str, token: str) -> None:
    """Handle 'no thanks' button -- confirm review."""
    _pending_review_text.pop(max_user_id, None)
    await _send(
        token,
        max_user_id,
        "\u0421\u043f\u0430\u0441\u0438\u0431\u043e \u0437\u0430 \u043e\u0442\u0437\u044b\u0432! \U0001f64f",
    )


async def handle_review_text_message(
    max_user_id: str, text: str, db: AsyncSession, token: str
) -> bool:
    """Handle incoming text message if user is in pending review text state.

    Returns True if the message was handled (was a review text), False otherwise.
    """
    booking_id = _pending_review_text.pop(max_user_id, None)
    if not booking_id:
        return False

    review_result = await db.execute(
        select(Review).where(Review.booking_id == booking_id)
    )
    review = review_result.scalar_one_or_none()
    if review:
        review.text = text[:500]
        review.updated_at = datetime.now(timezone.utc)
        await db.flush()

    await _send(
        token,
        max_user_id,
        "\u0421\u043f\u0430\u0441\u0438\u0431\u043e \u0437\u0430 \u043e\u0442\u0437\u044b\u0432! \U0001f64f",
    )
    return True


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
