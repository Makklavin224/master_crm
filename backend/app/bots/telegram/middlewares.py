"""aiogram middlewares for Telegram bot handlers.

DatabaseMiddleware injects an async DB session into handler data,
with automatic commit/rollback lifecycle.
"""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.core.database import async_session_factory


class DatabaseMiddleware(BaseMiddleware):
    """Inject database session into handler data with commit/rollback."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with async_session_factory() as session:
            data["db"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
