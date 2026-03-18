"""Handler for VK message_event (callback button clicks).

Handles: today, link, booking:{id}, cancel:{id}, cancel_client:{id}
Acknowledges callbacks with messages.sendMessageEventAnswer.
"""

import json
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

VK_API_URL = "https://api.vk.com/method/"
VK_API_VERSION = "5.199"


async def handle_callback(body: dict, db: AsyncSession) -> None:
    """Handle VK message_event (callback button click)."""
    obj = body.get("object", {})
    user_id = str(obj.get("user_id", ""))
    event_id = obj.get("event_id", "")
    peer_id = obj.get("peer_id", "")
    payload = obj.get("payload", {})

    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (json.JSONDecodeError, TypeError):
            payload = {}

    cmd = payload.get("cmd", "")
    vk_token = settings.vk_group_token

    if cmd == "today":
        await _handle_today_callback(user_id, vk_token, db)
    elif cmd == "link":
        await _handle_link_callback(user_id, vk_token, db)
    elif cmd.startswith("booking:"):
        booking_id_str = cmd.split(":", 1)[1]
        await _handle_booking_detail(user_id, booking_id_str, vk_token, db)
    elif cmd.startswith("cancel:"):
        booking_id_str = cmd.split(":", 1)[1]
        await _handle_cancel_booking(user_id, booking_id_str, vk_token, db)
    elif cmd.startswith("cancel_client:"):
        booking_id_str = cmd.split(":", 1)[1]
        await _handle_cancel_client(user_id, booking_id_str, vk_token, db)

    # Acknowledge callback event
    await _acknowledge_event(vk_token, event_id, user_id, peer_id)


async def _acknowledge_event(
    token: str, event_id: str, user_id: str, peer_id: int | str
) -> None:
    """Acknowledge VK callback event with sendMessageEventAnswer."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{VK_API_URL}messages.sendMessageEventAnswer",
                data={
                    "event_id": event_id,
                    "user_id": int(user_id),
                    "peer_id": int(peer_id),
                    "event_data": json.dumps(
                        {"type": "show_snackbar", "text": "\u041e\u0431\u0440\u0430\u0431\u043e\u0442\u0430\u043d\u043e"}
                    ),
                    "access_token": token,
                    "v": VK_API_VERSION,
                },
            )
    except Exception:
        logger.exception("Failed to acknowledge VK callback event")


async def _send_message(
    token: str, user_id: str, text: str, keyboard: dict | None = None
) -> None:
    """Send a message via VK API."""
    data: dict = {
        "user_id": int(user_id),
        "message": text,
        "random_id": 0,
        "access_token": token,
        "v": VK_API_VERSION,
    }
    if keyboard:
        data["keyboard"] = json.dumps(keyboard)

    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{VK_API_URL}messages.send", data=data)
    except Exception:
        logger.exception("Failed to send VK message to %s", user_id)


async def _handle_today_callback(
    user_id: str, token: str, db: AsyncSession
) -> None:
    """Show today's bookings via callback."""
    result = await db.execute(
        select(Master).where(Master.vk_user_id == user_id)
    )
    master = result.scalar_one_or_none()
    if not master:
        await _send_message(
            token, user_id,
            "\u0412\u044b \u043d\u0435 "
            "\u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d\u044b. "
            "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /start",
        )
        return

    from app.bots.vk.handlers.today import format_today_bookings_text

    text = await format_today_bookings_text(db, master)
    await _send_message(token, user_id, text)


async def _handle_link_callback(
    user_id: str, token: str, db: AsyncSession
) -> None:
    """Show booking link via callback."""
    result = await db.execute(
        select(Master).where(Master.vk_user_id == user_id)
    )
    master = result.scalar_one_or_none()
    if not master:
        await _send_message(
            token, user_id,
            "\u0412\u044b \u043d\u0435 "
            "\u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d\u044b. "
            "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /start",
        )
        return

    link = f"https://vk.com/app{settings.vk_app_id}#master={master.id}"
    await _send_message(
        token, user_id,
        f"\u0412\u0430\u0448\u0430 \u0441\u0441\u044b\u043b\u043a\u0430 "
        f"\u0434\u043b\u044f \u0437\u0430\u043f\u0438\u0441\u0438:\n\n"
        f"{link}\n\n"
        f"\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 "
        f"\u0435\u0451 \u043a\u043b\u0438\u0435\u043d\u0442\u0430\u043c.",
    )


async def _handle_booking_detail(
    user_id: str, booking_id_str: str, token: str, db: AsyncSession
) -> None:
    """Show booking detail."""
    try:
        booking_id = uuid.UUID(booking_id_str)
    except ValueError:
        await _send_message(
            token, user_id,
            "\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.",
        )
        return

    result = await db.execute(
        select(Booking)
        .where(Booking.id == booking_id)
        .options(selectinload(Booking.client), selectinload(Booking.service))
    )
    booking = result.scalar_one_or_none()
    if not booking:
        await _send_message(
            token, user_id,
            "\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.",
        )
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
        f"\u0417\u0430\u043f\u0438\u0441\u044c "
        f"#{str(booking.id)[:8]}\n\n"
        f"\U0001f464 {client_name}\n"
        f"\U0001f487 {service_name}\n"
        f"\U0001f4c5 {date_str}\n"
        f"\U0001f550 {time_str}"
        f"{price_str}\n\n"
        f"\u0421\u0442\u0430\u0442\u0443\u0441: {status_text}"
    )

    # Action buttons
    import json as _json

    buttons = []
    if booking.status in ("confirmed", "pending"):
        buttons.append([
            {
                "action": {
                    "type": "callback",
                    "label": "\u274c \u041e\u0442\u043c\u0435\u043d\u0438\u0442\u044c",
                    "payload": _json.dumps({"cmd": f"cancel:{booking.id}"}),
                }
            },
            {
                "action": {
                    "type": "callback",
                    "label": "\U0001f4c5 \u041d\u0430\u0437\u0430\u0434",
                    "payload": _json.dumps({"cmd": "today"}),
                }
            },
        ])
    else:
        buttons.append([
            {
                "action": {
                    "type": "callback",
                    "label": "\U0001f4c5 \u041d\u0430\u0437\u0430\u0434",
                    "payload": _json.dumps({"cmd": "today"}),
                }
            },
        ])

    keyboard = {"inline": True, "buttons": buttons}
    await _send_message(token, user_id, text, keyboard)


async def _handle_cancel_booking(
    user_id: str, booking_id_str: str, token: str, db: AsyncSession
) -> None:
    """Cancel a booking by master."""
    try:
        booking_id = uuid.UUID(booking_id_str)
    except ValueError:
        await _send_message(
            token, user_id,
            "\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.",
        )
        return

    try:
        await cancel_booking(
            db=db,
            booking_id=booking_id,
            cancelled_by="master",
        )
        import json as _json

        keyboard = {
            "inline": True,
            "buttons": [[
                {
                    "action": {
                        "type": "callback",
                        "label": "\U0001f4c5 \u041a \u0437\u0430\u043f\u0438\u0441\u044f\u043c",
                        "payload": _json.dumps({"cmd": "today"}),
                    }
                },
            ]],
        }
        await _send_message(
            token, user_id,
            "\u2705 \u0417\u0430\u043f\u0438\u0441\u044c "
            "\u043e\u0442\u043c\u0435\u043d\u0435\u043d\u0430.\n\n"
            "\u041a\u043b\u0438\u0435\u043d\u0442 "
            "\u043f\u043e\u043b\u0443\u0447\u0438\u0442 "
            "\u0443\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u0435.",
            keyboard,
        )
    except Exception:
        logger.exception("Failed to cancel booking %s via VK", booking_id_str)
        await _send_message(
            token, user_id,
            "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c "
            "\u043e\u0442\u043c\u0435\u043d\u0438\u0442\u044c "
            "\u0437\u0430\u043f\u0438\u0441\u044c.",
        )


async def _handle_cancel_client(
    user_id: str, booking_id_str: str, token: str, db: AsyncSession
) -> None:
    """Cancel a booking by client (with deadline enforcement)."""
    try:
        booking_id = uuid.UUID(booking_id_str)
    except ValueError:
        await _send_message(
            token, user_id,
            "\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.",
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
        await _send_message(
            token, user_id,
            "\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.",
        )
        return

    # Security: verify callback sender is the booking's client
    client_platform_result = await db.execute(
        select(ClientPlatform).where(
            ClientPlatform.client_id == booking.client_id,
            ClientPlatform.platform == "vk",
        )
    )
    client_platform = client_platform_result.scalar_one_or_none()
    if not client_platform or client_platform.platform_user_id != user_id:
        await _send_message(
            token, user_id,
            "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c "
            "\u043e\u0442\u043c\u0435\u043d\u0438\u0442\u044c "
            "\u0437\u0430\u043f\u0438\u0441\u044c.",
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
        await _send_message(
            token, user_id,
            "\u2705 \u0417\u0430\u043f\u0438\u0441\u044c \u043e\u0442\u043c\u0435\u043d\u0435\u043d\u0430.",
        )
    except HTTPException as exc:
        if exc.status_code == 400:
            await _send_message(
                token, user_id,
                "\u041e\u0442\u043c\u0435\u043d\u0430 "
                "\u043d\u0435\u0432\u043e\u0437\u043c\u043e\u0436\u043d\u0430. "
                "\u0421\u0440\u043e\u043a \u043e\u0442\u043c\u0435\u043d\u044b "
                "\u0438\u0441\u0442\u0451\u043a.",
            )
        else:
            await _send_message(
                token, user_id,
                "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c "
                "\u043e\u0442\u043c\u0435\u043d\u0438\u0442\u044c "
                "\u0437\u0430\u043f\u0438\u0441\u044c.",
            )
    except Exception:
        logger.exception(
            "Failed to cancel booking %s via VK client callback",
            booking_id_str,
        )
        await _send_message(
            token, user_id,
            "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c "
            "\u043e\u0442\u043c\u0435\u043d\u0438\u0442\u044c "
            "\u0437\u0430\u043f\u0438\u0441\u044c.",
        )
