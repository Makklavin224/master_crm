"""Handler for /today command in VK bot -- show today's bookings."""

import json
import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.booking import Booking
from app.models.master import Master

logger = logging.getLogger(__name__)

VK_API_URL = "https://api.vk.com/method/"
VK_API_VERSION = "5.199"


async def handle_today(body: dict, db: AsyncSession) -> None:
    """Show today's bookings for the master via VK."""
    message = body.get("object", {}).get("message", {})
    from_id = str(message.get("from_id", ""))

    if not from_id:
        return

    vk_token = settings.vk_group_token

    # Look up master
    result = await db.execute(
        select(Master).where(Master.vk_user_id == from_id)
    )
    master = result.scalar_one_or_none()
    if not master:
        await _send_message(
            vk_token, from_id,
            "\u0412\u044b \u043d\u0435 "
            "\u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d\u044b. "
            "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /start",
        )
        return

    text = await format_today_bookings_text(db, master)
    await _send_message(vk_token, from_id, text)


async def format_today_bookings_text(
    db: AsyncSession, master: Master
) -> str:
    """Format today's bookings as plain text. Reused by callback handler."""
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
        return (
            "\u0421\u0435\u0433\u043e\u0434\u043d\u044f "
            "\u0437\u0430\u043f\u0438\u0441\u0435\u0439 "
            "\u043d\u0435\u0442. \u041e\u0442\u043b\u0438\u0447\u043d\u044b\u0439 "
            "\u0434\u0435\u043d\u044c, \u0447\u0442\u043e\u0431\u044b "
            "\u043e\u0442\u0434\u043e\u0445\u043d\u0443\u0442\u044c "
            "\u0438\u043b\u0438 \u043f\u0440\u0438\u043d\u044f\u0442\u044c "
            "\u043d\u043e\u0432\u044b\u0445 "
            "\u043a\u043b\u0438\u0435\u043d\u0442\u043e\u0432."
        )

    date_str = now.strftime("%d.%m.%Y")
    lines = [f"\u0417\u0430\u043f\u0438\u0441\u0438 \u043d\u0430 {date_str}:\n"]
    for b in bookings:
        local_time = b.starts_at.astimezone(tz).strftime("%H:%M")
        client_name = b.client.name if b.client else "\u2014"
        service_name = b.service.name if b.service else "\u2014"
        lines.append(
            f"\U0001f550 {local_time} \u2014 {client_name}\n"
            f"\U0001f487 {service_name}"
        )
    return "\n\n".join(lines)


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
