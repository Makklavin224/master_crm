"""VK Bot module singleton.

No vkbottle Bot object -- uses raw VK API calls via httpx.
Registers VkAdapter with NotificationService when VK_GROUP_TOKEN is set.
Exports vk_token and process_vk_event() for webhook handler.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

# Guard: only register adapter when token is configured
vk_token: str | None = None

if settings.vk_group_token:
    vk_token = settings.vk_group_token

    from app.bots.common.notification import notification_service
    from app.bots.vk.adapter import VkAdapter

    notification_service.register_adapter("vk", VkAdapter(vk_token))
    logger.info("VK bot configured and adapter registered")
else:
    logger.warning("VK_GROUP_TOKEN not set -- VK bot is disabled")


async def process_vk_event(body: dict, db: AsyncSession) -> None:
    """Route incoming VK Callback API events to the correct handler."""
    event_type = body.get("type")

    if event_type == "message_new":
        message = body.get("object", {}).get("message", {})
        text = message.get("text", "").strip().lower()

        if text in ("/start", "\u043d\u0430\u0447\u0430\u0442\u044c"):
            from app.bots.vk.handlers.start import handle_start

            await handle_start(body, db)
        elif text == "/today":
            from app.bots.vk.handlers.today import handle_today

            await handle_today(body, db)
        elif text == "/link":
            from app.bots.vk.handlers.link import handle_link

            await handle_link(body, db)
        else:
            # Check if this is a pending review text response
            user_id = str(message.get("from_id", ""))
            original_text = message.get("text", "").strip()
            if user_id and original_text:
                from app.bots.vk.handlers.callbacks import handle_review_text_message

                await handle_review_text_message(user_id, original_text, db)

    elif event_type == "message_event":
        from app.bots.vk.handlers.callbacks import handle_callback

        await handle_callback(body, db)
