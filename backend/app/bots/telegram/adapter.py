"""TelegramAdapter: implements MessengerAdapter for the Telegram platform.

Uses aiogram Bot instance to send formatted HTML notifications
with inline keyboard action buttons.
"""

import logging

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bots.common.adapter import BookingNotification, MessengerAdapter

logger = logging.getLogger(__name__)


class TelegramAdapter(MessengerAdapter):
    """Sends booking notifications and messages via Telegram bot."""

    def __init__(self, bot) -> None:
        self._bot = bot

    async def send_booking_notification(
        self, notif: BookingNotification
    ) -> bool:
        """Format and send a booking notification to a master via Telegram."""
        text = self._format_notification(notif)
        keyboard = self._build_keyboard(notif)

        try:
            await self._bot.send_message(
                chat_id=notif.master_platform_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            return True
        except Exception:
            logger.exception(
                "Failed to send TG notification to %s",
                notif.master_platform_id,
            )
            return False

    async def send_message(
        self, platform_user_id: str, text: str
    ) -> bool:
        """Send a simple text message via Telegram."""
        try:
            await self._bot.send_message(
                chat_id=platform_user_id,
                text=text,
                parse_mode="HTML",
            )
            return True
        except Exception:
            logger.exception(
                "Failed to send TG message to %s", platform_user_id
            )
            return False

    @staticmethod
    def _format_notification(notif: BookingNotification) -> str:
        """Build HTML notification text based on notification type."""
        if notif.notification_type == "new":
            price_line = ""
            if notif.price is not None:
                price_line = f"\n<b>Price:</b> {notif.price // 100} rub"
            return (
                "<b>New booking!</b>\n\n"
                f"Client: {notif.client_name}\n"
                f"Service: {notif.service_name}\n"
                f"Date: {notif.booking_date}\n"
                f"Time: {notif.booking_time}"
                f"{price_line}"
            )
        elif notif.notification_type == "cancelled":
            return (
                "<b>Booking cancelled</b>\n\n"
                f"Client: {notif.client_name}\n"
                f"Date: {notif.booking_date} at {notif.booking_time}"
            )
        elif notif.notification_type == "rescheduled":
            return (
                "<b>Booking rescheduled</b>\n\n"
                f"Client: {notif.client_name}\n"
                f"Date: {notif.booking_date}\n"
                f"Time: {notif.booking_time}"
            )
        else:
            return (
                f"<b>Booking update</b>\n\n"
                f"Client: {notif.client_name}\n"
                f"Date: {notif.booking_date}\n"
                f"Time: {notif.booking_time}"
            )

    @staticmethod
    def _build_keyboard(notif: BookingNotification) -> InlineKeyboardMarkup:
        """Build inline keyboard with action buttons."""
        buttons = [
            [
                InlineKeyboardButton(
                    text="Details",
                    callback_data=f"booking:{notif.booking_id}",
                ),
                InlineKeyboardButton(
                    text="Schedule",
                    callback_data="today",
                ),
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
