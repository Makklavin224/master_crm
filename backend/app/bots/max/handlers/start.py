"""Handler for bot_started event and /start messages in MAX.

Two paths:
- bot_started / /start (no args): Master registration or welcome back
- /start with deep link payload: Client booking entry point
"""

import logging
import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.master import Master

logger = logging.getLogger(__name__)

BASE_URL = "https://platform-api.max.ru"


async def _send_message(
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


def _inline_keyboard(buttons: list[list[dict]]) -> list[dict]:
    """Build MAX inline keyboard attachment."""
    return [
        {
            "type": "inline_keyboard",
            "payload": {"buttons": buttons},
        }
    ]


async def handle_bot_started(
    body: dict, db: AsyncSession, token: str
) -> None:
    """Handle bot_started event -- master registration or welcome back.

    Also handles deep link payload if present.
    """
    user = body.get("user", {})
    max_user_id = str(user.get("user_id", ""))
    user_name = user.get("name", "Master")

    if not max_user_id:
        logger.warning("bot_started event without user_id")
        return

    # Check for deep link payload (startapp parameter)
    payload = body.get("payload")
    if payload:
        await _handle_deep_link(token, max_user_id, payload, db)
        return

    # Look up master by max_user_id
    result = await db.execute(
        select(Master).where(Master.max_user_id == max_user_id)
    )
    master = result.scalar_one_or_none()

    if master:
        # Welcome back with management options
        buttons = _master_buttons()
        await _send_message(
            token=token,
            chat_id=max_user_id,
            text=(
                f"<b>\u0421 \u0432\u043e\u0437\u0432\u0440\u0430\u0449\u0435\u043d\u0438\u0435\u043c, "
                f"{master.name}!</b>\n\n"
                "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435:"
            ),
            attachments=_inline_keyboard(buttons),
        )
    else:
        # Create new master
        master = Master(
            name=user_name,
            max_user_id=max_user_id,
        )
        db.add(master)
        await db.flush()

        buttons = _panel_buttons()
        await _send_message(
            token=token,
            chat_id=max_user_id,
            text=(
                "<b>\u0414\u043e\u0431\u0440\u043e "
                "\u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c "
                "\u0432 \u041c\u0430\u0441\u0442\u0435\u0440-CRM!</b>\n\n"
                "\u0412\u0430\u0448 \u0430\u043a\u043a\u0430\u0443\u043d\u0442 "
                "\u0441\u043e\u0437\u0434\u0430\u043d.\n\n"
                "\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u0442\u0435 "
                "\u0443\u0441\u043b\u0443\u0433\u0438 \u0438 "
                "\u0440\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435, "
                "\u0447\u0442\u043e\u0431\u044b \u043a\u043b\u0438\u0435\u043d\u0442\u044b "
                "\u043c\u043e\u0433\u043b\u0438 "
                "\u0437\u0430\u043f\u0438\u0441\u044b\u0432\u0430\u0442\u044c\u0441\u044f."
            ),
            attachments=_inline_keyboard(buttons),
        )
        logger.info(
            "New master registered via MAX: %s (max_user_id=%s)",
            master.id,
            max_user_id,
        )


async def handle_start_message(
    body: dict, db: AsyncSession, token: str
) -> None:
    """Handle /start text message -- same as bot_started but from message_created."""
    message = body.get("message", {})
    sender = message.get("sender", {})
    max_user_id = str(sender.get("user_id", ""))
    text = message.get("body", {}).get("text", "")

    if not max_user_id:
        return

    # Extract deep link from /start <payload>
    parts = text.strip().split(maxsplit=1)
    if len(parts) > 1:
        await _handle_deep_link(token, max_user_id, parts[1], db)
        return

    # No payload -- treat as regular bot_started
    user_name = sender.get("name", "Master")
    await handle_bot_started(
        {"user": {"user_id": max_user_id, "name": user_name}},
        db,
        token,
    )


async def _handle_deep_link(
    token: str, chat_id: str, payload: str, db: AsyncSession
) -> None:
    """Handle deep link with master_id -- show booking mini-app button."""
    try:
        master_id = uuid.UUID(payload.strip())
    except ValueError:
        await _send_message(
            token=token,
            chat_id=chat_id,
            text="\u041c\u0430\u0441\u0442\u0435\u0440 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d. \u041f\u0440\u043e\u0432\u0435\u0440\u044c\u0442\u0435 \u0441\u0441\u044b\u043b\u043a\u0443.",
        )
        return

    result = await db.execute(
        select(Master).where(
            Master.id == master_id, Master.is_active.is_(True)
        )
    )
    master = result.scalar_one_or_none()
    if not master:
        await _send_message(
            token=token,
            chat_id=chat_id,
            text="\u041c\u0430\u0441\u0442\u0435\u0440 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d. \u041f\u0440\u043e\u0432\u0435\u0440\u044c\u0442\u0435 \u0441\u0441\u044b\u043b\u043a\u0443.",
        )
        return

    mini_app_url = f"{settings.mini_app_url}?master={master_id}"
    buttons = [
        [
            {
                "type": "open_app",
                "text": "\U0001f4c5 \u0417\u0430\u043f\u0438\u0441\u0430\u0442\u044c\u0441\u044f",
                "url": mini_app_url,
            }
        ]
    ]
    await _send_message(
        token=token,
        chat_id=chat_id,
        text=(
            f"\u041e\u0442\u043a\u0440\u043e\u0439\u0442\u0435 "
            f"\u043c\u0438\u043d\u0438-\u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0435 "
            f"\u0434\u043b\u044f \u0437\u0430\u043f\u0438\u0441\u0438 "
            f"\u043a <b>{master.name}</b>:"
        ),
        attachments=_inline_keyboard(buttons),
    )


def _master_buttons() -> list[list[dict]]:
    """Build inline keyboard buttons for master welcome back."""
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


def _panel_buttons() -> list[list[dict]]:
    """Build inline keyboard buttons with panel link for new master."""
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
    return buttons
