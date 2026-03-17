import logging
from contextlib import asynccontextmanager

from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_v1_router
from app.bots.telegram.bot import bot, dp
from app.core.config import settings
from app.core.database import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify DB connection
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))

    # Register TG webhook
    if bot and settings.base_webhook_url:
        webhook_url = f"{settings.base_webhook_url}/webhook/telegram"
        await bot.set_webhook(
            webhook_url,
            secret_token=settings.tg_webhook_secret,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"],
        )
        logger.info("Telegram webhook registered: %s", webhook_url)

    yield

    # Shutdown: clean up bot and engine
    if bot:
        try:
            await bot.delete_webhook()
        except Exception:
            logger.exception("Failed to delete TG webhook")
        await bot.session.close()
    await engine.dispose()


def create_app() -> FastAPI:
    application = FastAPI(
        title="Master CRM API",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_v1_router, prefix="/api/v1")

    # Telegram webhook endpoint
    @application.post("/webhook/telegram")
    async def telegram_webhook(
        request: Request,
        x_telegram_bot_api_secret_token: str | None = Header(None),
    ):
        """Process incoming Telegram updates via webhook."""
        if x_telegram_bot_api_secret_token != settings.tg_webhook_secret:
            raise HTTPException(status_code=403, detail="Invalid secret token")

        if not bot or not dp:
            raise HTTPException(
                status_code=503, detail="Bot not configured"
            )

        update_data = await request.json()
        update = Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
        return {"ok": True}

    return application


app = create_app()
