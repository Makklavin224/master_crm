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
        """Build HTML notification text based on notification type (Russian)."""
        if notif.notification_type == "new":
            price_line = ""
            if notif.price is not None:
                rub = notif.price // 100
                price_line = f"\n\U0001f4b0 {rub} \u20bd"
            return (
                f"<b>\u2728 \u041d\u043e\u0432\u0430\u044f \u0437\u0430\u043f\u0438\u0441\u044c!</b>\n\n"
                f"\U0001f464 {notif.client_name}\n"
                f"\U0001f487 {notif.service_name}\n"
                f"\U0001f4c5 {notif.booking_date}\n"
                f"\U0001f550 {notif.booking_time}"
                f"{price_line}"
            )
        elif notif.notification_type == "cancelled":
            return (
                f"<b>\u274c \u0417\u0430\u043f\u0438\u0441\u044c \u043e\u0442\u043c\u0435\u043d\u0435\u043d\u0430</b>\n\n"
                f"\U0001f464 {notif.client_name}\n"
                f"\U0001f4c5 {notif.booking_date} \u0432 {notif.booking_time}"
            )
        elif notif.notification_type == "rescheduled":
            return (
                f"<b>\U0001f504 \u0417\u0430\u043f\u0438\u0441\u044c \u043f\u0435\u0440\u0435\u043d\u0435\u0441\u0435\u043d\u0430</b>\n\n"
                f"\U0001f464 {notif.client_name}\n"
                f"\U0001f4c5 {notif.booking_date}\n"
                f"\U0001f550 {notif.booking_time}"
            )
        else:
            return (
                f"<b>\u0417\u0430\u043f\u0438\u0441\u044c</b>\n\n"
                f"\U0001f464 {notif.client_name}\n"
                f"\U0001f4c5 {notif.booking_date}\n"
                f"\U0001f550 {notif.booking_time}"
            )

    @staticmethod
    def _build_keyboard(notif: BookingNotification) -> InlineKeyboardMarkup:
        """Build inline keyboard with action buttons."""
        buttons = [
            [
                InlineKeyboardButton(
                    text="\U0001f4cb \u041f\u043e\u0434\u0440\u043e\u0431\u043d\u0435\u0435",
                    callback_data=f"booking:{notif.booking_id}",
                ),
                InlineKeyboardButton(
                    text="\U0001f4c5 \u0420\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435",
                    callback_data="today",
                ),
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
