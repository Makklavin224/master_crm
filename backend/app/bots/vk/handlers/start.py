"""Handler for /start command and "Начать" button in VK bot.

Two paths:
- First-time user: create Master with vk_user_id
- Returning user: welcome back with action keyboard
"""

import json
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.master import Master

logger = logging.getLogger(__name__)

VK_API_URL = "https://api.vk.com/method/"
VK_API_VERSION = "5.199"


async def handle_start(body: dict, db: AsyncSession) -> None:
    """Handle /start or 'Начать' message from VK user."""
    message = body.get("object", {}).get("message", {})
    from_id = str(message.get("from_id", ""))

    if not from_id:
        return

    vk_token = settings.vk_group_token

    # Check if master already registered
    result = await db.execute(
        select(Master).where(Master.vk_user_id == from_id)
    )
    master = result.scalar_one_or_none()

    if master:
        # Welcome back with management keyboard
        keyboard = _master_keyboard()
        text = (
            f"\u0421 \u0432\u043e\u0437\u0432\u0440\u0430\u0449\u0435\u043d\u0438\u0435\u043c, "
            f"{master.name}!\n\n"
            "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435:"
        )
    else:
        # Get VK user info for name
        user_name = "Master"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{VK_API_URL}users.get",
                    data={
                        "user_ids": from_id,
                        "access_token": vk_token,
                        "v": VK_API_VERSION,
                    },
                )
                data = resp.json()
                users = data.get("response", [])
                if users:
                    user_name = f"{users[0].get('first_name', '')} {users[0].get('last_name', '')}".strip() or "Master"
        except Exception:
            logger.exception("Failed to fetch VK user info for %s", from_id)

        # Create new master
        master = Master(
            name=user_name,
            vk_user_id=from_id,
        )
        db.add(master)
        await db.flush()

        keyboard = _master_keyboard()
        text = (
            "\u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c "
            "\u0432 \u041c\u0430\u0441\u0442\u0435\u0440-CRM!\n\n"
            "\u0412\u0430\u0448 \u0430\u043a\u043a\u0430\u0443\u043d\u0442 "
            "\u0441\u043e\u0437\u0434\u0430\u043d.\n\n"
            "\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u0442\u0435 "
            "\u0443\u0441\u043b\u0443\u0433\u0438 \u0438 "
            "\u0440\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435, "
            "\u0447\u0442\u043e\u0431\u044b \u043a\u043b\u0438\u0435\u043d\u0442\u044b "
            "\u043c\u043e\u0433\u043b\u0438 "
            "\u0437\u0430\u043f\u0438\u0441\u044b\u0432\u0430\u0442\u044c\u0441\u044f."
        )
        logger.info(
            "New master registered via VK: %s (vk_user_id=%s)",
            master.id,
            from_id,
        )

    # Send response
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{VK_API_URL}messages.send",
                data={
                    "user_id": int(from_id),
                    "message": text,
                    "random_id": 0,
                    "keyboard": json.dumps(keyboard),
                    "access_token": vk_token,
                    "v": VK_API_VERSION,
                },
            )
    except Exception:
        logger.exception("Failed to send VK start response to %s", from_id)


def _master_keyboard() -> dict:
    """Build inline keyboard for master welcome/welcome back."""
    return {
        "inline": True,
        "buttons": [
            [
                {
                    "action": {
                        "type": "callback",
                        "label": "\U0001f4c5 \u0417\u0430\u043f\u0438\u0441\u0438 \u043d\u0430 \u0441\u0435\u0433\u043e\u0434\u043d\u044f",
                        "payload": json.dumps({"cmd": "today"}),
                    }
                },
                {
                    "action": {
                        "type": "callback",
                        "label": "\U0001f517 \u041c\u043e\u044f \u0441\u0441\u044b\u043b\u043a\u0430",
                        "payload": json.dumps({"cmd": "link"}),
                    }
                },
            ],
        ],
    }
