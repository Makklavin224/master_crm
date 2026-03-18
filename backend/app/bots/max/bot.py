"""MAX Bot module singleton and update router.

Module-level singleton guarded by token presence:
- When MAX_BOT_TOKEN is empty, bot_token is None (allows app to start without MAX).
- When configured, MaxAdapter is registered with NotificationService.
- No Dispatcher or Bot object from maxapi -- uses httpx + raw JSON.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

# Guard: only configure when token is present
bot_token: str | None = None

if settings.max_bot_token:
    bot_token = settings.max_bot_token

    # Register MaxAdapter with NotificationService
    from app.bots.common.notification import notification_service
    from app.bots.max.adapter import MaxAdapter

    notification_service.register_adapter("max", MaxAdapter(bot_token))

    logger.info("MAX bot configured and adapter registered")
else:
    logger.warning(
        "MAX_BOT_TOKEN not set -- MAX bot is disabled"
    )


async def process_max_update(body: dict, db: AsyncSession) -> None:
    """Route incoming MAX webhook update to the correct handler.

    Called from the FastAPI webhook endpoint with a DB session.
    """
    if not bot_token:
        logger.warning("MAX update received but bot_token not configured")
        return

    update_type = body.get("update_type")

    if update_type == "bot_started":
        from app.bots.max.handlers.start import handle_bot_started

        await handle_bot_started(body, db, bot_token)

    elif update_type == "message_created":
        # Route based on message text
        message = body.get("message", {})
        text = message.get("body", {}).get("text", "").strip()

        if text.startswith("/start"):
            from app.bots.max.handlers.start import handle_start_message

            await handle_start_message(body, db, bot_token)
        elif text.startswith("/today"):
            from app.bots.max.handlers.today import handle_today

            await handle_today(body, db, bot_token)
        elif text.startswith("/link"):
            from app.bots.max.handlers.link import handle_link

            await handle_link(body, db, bot_token)
        else:
            logger.debug("Unhandled MAX message: %s", text[:50] if text else "(empty)")

    elif update_type == "message_callback":
        from app.bots.max.handlers.callbacks import handle_callback

        await handle_callback(body, db, bot_token)

    else:
        logger.debug("Unhandled MAX update type: %s", update_type)
