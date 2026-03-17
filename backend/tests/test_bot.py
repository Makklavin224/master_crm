"""Tests for Telegram bot integration: webhook, adapter pattern, notifications."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.bots.common.adapter import BookingNotification, MessengerAdapter
from app.bots.common.notification import NotificationService
from app.bots.telegram.adapter import TelegramAdapter


# ---------------------------------------------------------------------------
# Webhook endpoint tests
# ---------------------------------------------------------------------------


class TestWebhookEndpoint:
    """POST /webhook/telegram secret token validation."""

    @pytest.fixture
    def webhook_app(self):
        """App for webhook tests."""
        from app.main import create_app

        return create_app()

    async def test_webhook_missing_secret_returns_403(self, webhook_app):
        """POST /webhook/telegram with no secret header returns 403."""
        async with AsyncClient(
            transport=ASGITransport(app=webhook_app), base_url="http://test"
        ) as ac:
            resp = await ac.post(
                "/webhook/telegram",
                json={"update_id": 1},
            )
        assert resp.status_code == 403

    async def test_webhook_invalid_secret_returns_403(self, webhook_app):
        """POST /webhook/telegram with wrong secret returns 403."""
        async with AsyncClient(
            transport=ASGITransport(app=webhook_app), base_url="http://test"
        ) as ac:
            resp = await ac.post(
                "/webhook/telegram",
                json={"update_id": 1},
                headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-token"},
            )
        assert resp.status_code == 403

    async def test_webhook_valid_secret_returns_200(self):
        """POST /webhook/telegram with valid secret + update JSON returns 200."""
        mock_bot = AsyncMock()
        mock_dp = AsyncMock()
        mock_dp.feed_update = AsyncMock()

        with (
            patch("app.main.settings") as mock_settings,
            patch("app.main.bot", mock_bot),
            patch("app.main.dp", mock_dp),
            patch("app.main.Update") as mock_update_cls,
        ):
            mock_settings.tg_webhook_secret = "test-secret-token"
            mock_settings.tg_bot_token = "fake:token"
            mock_settings.base_webhook_url = ""
            mock_settings.allowed_origins = ["*"]

            # Mock Update.model_validate to return a mock update
            mock_update = MagicMock()
            mock_update_cls.model_validate.return_value = mock_update

            from app.main import create_app

            test_app = create_app()
            async with AsyncClient(
                transport=ASGITransport(app=test_app), base_url="http://test"
            ) as ac:
                resp = await ac.post(
                    "/webhook/telegram",
                    json={"update_id": 123},
                    headers={
                        "X-Telegram-Bot-Api-Secret-Token": "test-secret-token"
                    },
                )

        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True


# ---------------------------------------------------------------------------
# NotificationService tests
# ---------------------------------------------------------------------------


class TestNotificationService:
    """NotificationService routes to correct adapter by platform."""

    def test_register_adapter(self):
        """register_adapter stores adapter for platform key."""
        ns = NotificationService()
        mock_adapter = MagicMock(spec=MessengerAdapter)
        ns.register_adapter("telegram", mock_adapter)
        assert "telegram" in ns._adapters
        assert ns._adapters["telegram"] is mock_adapter

    async def test_routes_to_correct_adapter(self):
        """send_booking_notification calls the right adapter."""
        ns = NotificationService()
        tg_adapter = AsyncMock(spec=MessengerAdapter)
        tg_adapter.send_booking_notification = AsyncMock(return_value=True)
        vk_adapter = AsyncMock(spec=MessengerAdapter)
        vk_adapter.send_booking_notification = AsyncMock(return_value=True)

        ns.register_adapter("telegram", tg_adapter)
        ns.register_adapter("vk", vk_adapter)

        notif = BookingNotification(
            master_platform_id="12345",
            client_name="Test Client",
            service_name="Haircut",
            booking_time="14:00",
            booking_date="25.03.2026",
            booking_id="abc-123",
            notification_type="new",
            price=250000,
        )

        result = await ns.send_booking_notification("telegram", notif)
        assert result is True
        tg_adapter.send_booking_notification.assert_called_once_with(notif)
        vk_adapter.send_booking_notification.assert_not_called()

    async def test_unknown_platform_returns_false(self):
        """send_booking_notification for unknown platform returns False."""
        ns = NotificationService()
        notif = BookingNotification(
            master_platform_id="12345",
            client_name="Client",
            service_name="Service",
            booking_time="10:00",
            booking_date="25.03.2026",
            booking_id="xyz",
            notification_type="new",
        )
        result = await ns.send_booking_notification("whatsapp", notif)
        assert result is False


# ---------------------------------------------------------------------------
# MessengerAdapter / TelegramAdapter tests
# ---------------------------------------------------------------------------


class TestTelegramAdapter:
    """TelegramAdapter implements MessengerAdapter interface."""

    def test_implements_messenger_adapter(self):
        """TelegramAdapter is a subclass of MessengerAdapter."""
        assert issubclass(TelegramAdapter, MessengerAdapter)

    def test_has_required_methods(self):
        """TelegramAdapter has send_booking_notification and send_message."""
        mock_bot = MagicMock()
        adapter = TelegramAdapter(mock_bot)
        assert hasattr(adapter, "send_booking_notification")
        assert hasattr(adapter, "send_message")
        assert callable(adapter.send_booking_notification)
        assert callable(adapter.send_message)

    async def test_send_booking_notification_new(self):
        """send_booking_notification formats and sends 'new' booking message."""
        mock_bot = AsyncMock()
        mock_bot.send_message = AsyncMock()
        adapter = TelegramAdapter(mock_bot)

        notif = BookingNotification(
            master_platform_id="12345",
            client_name="Anna",
            service_name="Haircut",
            booking_time="14:00",
            booking_date="25.03.2026",
            booking_id="abc-def-123",
            notification_type="new",
            price=250000,
        )

        result = await adapter.send_booking_notification(notif)
        assert result is True
        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args
        # Verify it sends to the right chat_id
        assert call_kwargs.kwargs.get("chat_id") == "12345" or call_kwargs[1].get("chat_id") == "12345"

    async def test_send_booking_notification_cancelled(self):
        """send_booking_notification formats cancelled notification."""
        mock_bot = AsyncMock()
        mock_bot.send_message = AsyncMock()
        adapter = TelegramAdapter(mock_bot)

        notif = BookingNotification(
            master_platform_id="12345",
            client_name="Anna",
            service_name="Haircut",
            booking_time="14:00",
            booking_date="25.03.2026",
            booking_id="abc-def-123",
            notification_type="cancelled",
        )

        result = await adapter.send_booking_notification(notif)
        assert result is True
        mock_bot.send_message.assert_called_once()

    async def test_send_message(self):
        """send_message sends text to platform user."""
        mock_bot = AsyncMock()
        mock_bot.send_message = AsyncMock()
        adapter = TelegramAdapter(mock_bot)

        result = await adapter.send_message("12345", "Hello!")
        assert result is True
        mock_bot.send_message.assert_called_once()
