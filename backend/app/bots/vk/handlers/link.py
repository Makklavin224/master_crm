"""Handler for /link command in VK bot -- generate VK mini-app booking link."""

import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.master import Master

logger = logging.getLogger(__name__)

VK_API_URL = "https://api.vk.com/method/"
VK_API_VERSION = "5.199"


async def handle_link(body: dict, db: AsyncSession) -> None:
    """Send the master their VK mini-app booking deep link."""
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
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{VK_API_URL}messages.send",
                    data={
                        "user_id": int(from_id),
                        "message": (
                            "\u0412\u044b \u043d\u0435 "
                            "\u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d\u044b. "
                            "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /start"
                        ),
                        "random_id": 0,
                        "access_token": vk_token,
                        "v": VK_API_VERSION,
                    },
                )
        except Exception:
            logger.exception("Failed to send VK message to %s", from_id)
        return

    # Generate VK mini-app deep link
    link = f"https://vk.com/app{settings.vk_app_id}#master={master.id}"

    text = (
        f"\u0412\u0430\u0448\u0430 \u0441\u0441\u044b\u043b\u043a\u0430 "
        f"\u0434\u043b\u044f \u0437\u0430\u043f\u0438\u0441\u0438:\n\n"
        f"{link}\n\n"
        f"\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 "
        f"\u0435\u0451 \u043a\u043b\u0438\u0435\u043d\u0442\u0430\u043c "
        f"\u2014 \u043e\u043d\u0438 \u0441\u043c\u043e\u0433\u0443\u0442 "
        f"\u0437\u0430\u043f\u0438\u0441\u0430\u0442\u044c\u0441\u044f "
        f"\u0447\u0435\u0440\u0435\u0437 "
        f"\u043c\u0438\u043d\u0438-\u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0435."
    )

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{VK_API_URL}messages.send",
                data={
                    "user_id": int(from_id),
                    "message": text,
                    "random_id": 0,
                    "access_token": vk_token,
                    "v": VK_API_VERSION,
                },
            )
    except Exception:
        logger.exception("Failed to send VK link message to %s", from_id)
