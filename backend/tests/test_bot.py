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


# ---------------------------------------------------------------------------
# Handler tests (unit tests with mocked message/db)
# ---------------------------------------------------------------------------


class TestStartHandler:
    """Tests for /start command handler."""

    async def test_start_creates_master(self):
        """
        /start without deep link creates a new Master
        with tg_user_id set.
        """
        from app.bots.telegram.handlers.start import start_no_link

        # Mock message
        message = AsyncMock()
        message.from_user = MagicMock()
        message.from_user.id = 123456
        message.from_user.full_name = "Test Master"
        message.answer = AsyncMock()

        # Mock DB session -- no existing master
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        db.add = MagicMock()
        db.flush = AsyncMock()

        await start_no_link(message, db)

        # Verify master was added to db
        db.add.assert_called_once()
        added_master = db.add.call_args[0][0]
        assert added_master.tg_user_id == "123456"
        assert added_master.name == "Test Master"

        # Verify welcome message was sent
        message.answer.assert_called_once()
        call_kwargs = message.answer.call_args
        assert "CRM" in call_kwargs[0][0] or "CRM" in call_kwargs.kwargs.get("text", call_kwargs[0][0])

    async def test_start_existing_master_shows_welcome_back(self):
        """/start for already registered master shows welcome back."""
        from app.bots.telegram.handlers.start import start_no_link

        mock_master = MagicMock()
        mock_master.name = "Existing Master"

        message = AsyncMock()
        message.from_user = MagicMock()
        message.from_user.id = 123456
        message.answer = AsyncMock()

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_master
        db.execute = AsyncMock(return_value=mock_result)

        await start_no_link(message, db)

        # Should NOT add a new master
        db.add.assert_not_called()

        # Should send welcome back
        message.answer.assert_called_once()

    async def test_start_deep_link_valid_master(self):
        """/start with valid master UUID shows booking button."""
        import uuid

        from app.bots.telegram.handlers.start import start_with_deep_link

        master_id = uuid.uuid4()
        mock_master = MagicMock()
        mock_master.name = "Master Name"
        mock_master.id = master_id

        message = AsyncMock()
        message.from_user = MagicMock()
        message.from_user.id = 789
        message.answer = AsyncMock()

        command = MagicMock()
        command.args = str(master_id)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_master
        db.execute = AsyncMock(return_value=mock_result)

        await start_with_deep_link(message, command, db)

        message.answer.assert_called_once()

    async def test_start_deep_link_invalid_uuid(self):
        """/start with invalid UUID shows error message."""
        from app.bots.telegram.handlers.start import start_with_deep_link

        message = AsyncMock()
        message.from_user = MagicMock()
        message.from_user.id = 789
        message.answer = AsyncMock()

        command = MagicMock()
        command.args = "not-a-uuid"

        db = AsyncMock()

        await start_with_deep_link(message, command, db)

        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        # Should contain "not found" message
        assert "\u043d\u0435" in call_text.lower() or "not found" in call_text.lower()


class TestTodayHandler:
    """Tests for /today command handler."""

    async def test_today_not_registered(self):
        """/today for unregistered user shows registration prompt."""
        from app.bots.telegram.handlers.today import cmd_today

        message = AsyncMock()
        message.from_user = MagicMock()
        message.from_user.id = 999
        message.answer = AsyncMock()

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        await cmd_today(message, db)

        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "/start" in call_text

    async def test_today_no_bookings(self):
        """/today with no bookings shows empty message."""
        from app.bots.telegram.handlers.today import cmd_today

        mock_master = MagicMock()
        mock_master.id = "test-id"
        mock_master.timezone = "Europe/Moscow"

        message = AsyncMock()
        message.from_user = MagicMock()
        message.from_user.id = 123
        message.answer = AsyncMock()

        # First call returns master, second call returns empty bookings
        db = AsyncMock()
        master_result = MagicMock()
        master_result.scalar_one_or_none.return_value = mock_master
        bookings_result = MagicMock()
        bookings_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(side_effect=[master_result, bookings_result])

        await cmd_today(message, db)

        message.answer.assert_called_once()


class TestLinkHandler:
    """Tests for /link command handler."""

    async def test_link_returns_deep_link(self):
        """/link returns t.me/bot?start=master_id format."""
        import uuid

        from app.bots.telegram.handlers.link import cmd_link

        master_id = uuid.uuid4()
        mock_master = MagicMock()
        mock_master.id = master_id

        # Mock bot.get_me()
        mock_bot_info = MagicMock()
        mock_bot_info.username = "TestBot"

        message = AsyncMock()
        message.from_user = MagicMock()
        message.from_user.id = 123
        message.answer = AsyncMock()
        message.bot = AsyncMock()
        message.bot.get_me = AsyncMock(return_value=mock_bot_info)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_master
        db.execute = AsyncMock(return_value=mock_result)

        await cmd_link(message, db)

        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert f"t.me/TestBot?start={master_id}" in call_text


class TestBookingNotificationIntegration:
    """Tests for booking notification integration with booking_service."""

    async def test_booking_notification_sent_on_create(self):
        """Creating a booking triggers notification to master."""
        from app.services.booking_service import _notify_master

        # Create mock booking
        mock_booking = MagicMock()
        mock_booking.id = "booking-123"
        mock_booking.master_id = "master-456"
        mock_booking.service_id = "svc-789"
        mock_booking.client_id = "client-000"
        mock_booking.starts_at = MagicMock()
        mock_booking.starts_at.strftime = MagicMock(return_value="14:00")
        mock_booking.service = MagicMock()
        mock_booking.service.name = "Haircut"
        mock_booking.service.price = 250000
        mock_booking.client = MagicMock()
        mock_booking.client.name = "Anna"

        # Mock master with tg_user_id
        mock_master = MagicMock()
        mock_master.tg_user_id = "12345"

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_master
        db.execute = AsyncMock(return_value=mock_result)

        # Mock the notification service
        with patch(
            "app.services.booking_service.notification_service"
        ) as mock_ns:
            mock_ns.send_booking_notification = AsyncMock(return_value=True)
            await _notify_master(db, mock_booking, "new")
            mock_ns.send_booking_notification.assert_called_once()

    async def test_notification_failure_does_not_raise(self):
        """Notification failure is swallowed, does not break booking flow."""
        from app.services.booking_service import _notify_master

        mock_booking = MagicMock()
        mock_booking.id = "booking-123"
        mock_booking.master_id = "master-456"
        mock_booking.service_id = "svc-789"
        mock_booking.client_id = "client-000"
        mock_booking.starts_at = MagicMock()
        mock_booking.starts_at.strftime = MagicMock(return_value="14:00")
        mock_booking.service = MagicMock()
        mock_booking.service.name = "Haircut"
        mock_booking.service.price = 250000
        mock_booking.client = MagicMock()
        mock_booking.client.name = "Anna"

        mock_master = MagicMock()
        mock_master.tg_user_id = "12345"

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_master
        db.execute = AsyncMock(return_value=mock_result)

        with patch(
            "app.services.booking_service.notification_service"
        ) as mock_ns:
            mock_ns.send_booking_notification = AsyncMock(
                side_effect=Exception("TG API down")
            )
            # Should NOT raise
            await _notify_master(db, mock_booking, "new")
