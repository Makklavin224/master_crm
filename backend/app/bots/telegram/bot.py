"""Telegram Bot + Dispatcher singletons.

Module-level singletons guarded by token presence:
- When TG_BOT_TOKEN is empty, bot and dp are None (allows tests without TG token).
- When configured, handler routers and middlewares are registered.
"""

import logging

from aiogram import Bot, Dispatcher

from app.core.config import settings

logger = logging.getLogger(__name__)

# Guard: only create bot/dp when token is configured
bot: Bot | None = None
dp: Dispatcher | None = None

if settings.tg_bot_token:
    bot = Bot(token=settings.tg_bot_token)
    dp = Dispatcher()

    # Register handler routers
    from app.bots.telegram.handlers.callbacks import router as callbacks_router
    from app.bots.telegram.handlers.link import router as link_router
    from app.bots.telegram.handlers.login import router as login_router
    from app.bots.telegram.handlers.settings import router as settings_router
    from app.bots.telegram.handlers.start import router as start_router
    from app.bots.telegram.handlers.today import router as today_router

    dp.include_routers(
        start_router,
        login_router,
        today_router,
        link_router,
        settings_router,
        callbacks_router,
    )

    # Register database middleware on message and callback_query
    from app.bots.telegram.middlewares import DatabaseMiddleware

    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())

    # Register TelegramAdapter with NotificationService
    from app.bots.common.notification import notification_service
    from app.bots.telegram.adapter import TelegramAdapter

    notification_service.register_adapter("telegram", TelegramAdapter(bot))

    logger.info("Telegram bot configured and handlers registered")
else:
    logger.warning(
        "TG_BOT_TOKEN not set -- Telegram bot is disabled"
    )
