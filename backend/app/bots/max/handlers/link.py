"""Handler for /link command in MAX -- generate shareable booking deep link."""

import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.master import Master

logger = logging.getLogger(__name__)

BASE_URL = "https://platform-api.max.ru"


async def handle_link(
    body: dict, db: AsyncSession, token: str
) -> None:
    """Send the master their shareable MAX booking deep link."""
    message = body.get("message", {})
    sender = message.get("sender", {})
    max_user_id = str(sender.get("user_id", ""))

    if not max_user_id:
        return

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
            f"\u0435\u0451 \u043a\u043b\u0438\u0435\u043d\u0442\u0430\u043c "
            f"\u2014 \u043e\u043d\u0438 \u0441\u043c\u043e\u0433\u0443\u0442 "
            f"\u0437\u0430\u043f\u0438\u0441\u0430\u0442\u044c\u0441\u044f "
            f"\u0447\u0435\u0440\u0435\u0437 "
            f"\u043c\u0438\u043d\u0438-\u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0435."
        ),
    )


async def _send(
    token: str,
    chat_id: str,
    text: str,
) -> None:
    """Send a message via MAX Bot API."""
    headers = {"Authorization": f"access_token={token}"}
    payload: dict = {"text": text, "format": "html"}

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
