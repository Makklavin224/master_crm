import logging
from contextlib import asynccontextmanager

from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy import text

from app.api.v1.router import api_v1_router
from app.bots.telegram.bot import bot, dp
from app.core.config import settings
from app.core.database import async_session_factory, engine

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

    # Robokassa ResultURL webhook (public, security via HMAC signature)
    @application.post("/webhook/robokassa/result")
    async def robokassa_result_callback(request: Request):
        """Process Robokassa ResultURL callback.

        Robokassa sends form data with OutSum, InvId, SignatureValue,
        and optional Shp_* custom params. Security is via HMAC signature
        verification, not auth tokens.
        """
        form_data = await request.form()

        out_sum = form_data.get("OutSum", "")
        inv_id_str = form_data.get("InvId", "")
        signature = form_data.get("SignatureValue", "")

        # Extract Shp_ params
        shp_params = {}
        for key in form_data:
            if key.startswith("Shp_"):
                shp_params[key] = form_data[key]

        # Validate required fields
        master_id = shp_params.get("Shp_master_id")
        if not master_id or not inv_id_str or not signature:
            return PlainTextResponse(
                "missing required parameters", status_code=400
            )

        try:
            inv_id = int(inv_id_str)
        except (ValueError, TypeError):
            return PlainTextResponse(
                "invalid InvId", status_code=400
            )

        from app.services.payment_service import PaymentService

        async with async_session_factory() as session:
            try:
                success = await PaymentService.handle_robokassa_callback(
                    db=session,
                    master_id=master_id,
                    inv_id=inv_id,
                    out_sum=out_sum,
                    signature=signature,
                    shp_params=shp_params,
                )
                await session.commit()
            except Exception:
                await session.rollback()
                logger.exception("Robokassa callback error for InvId=%s", inv_id_str)
                return PlainTextResponse(
                    "internal error", status_code=500
                )

        if success:
            return PlainTextResponse(f"OK{inv_id}")
        else:
            return PlainTextResponse(
                "signature verification failed", status_code=403
            )

    return application


app = create_app()
