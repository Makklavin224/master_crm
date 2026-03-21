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

    async def send_payment_link(
        self,
        platform_user_id: str,
        payment_url: str,
        service_name: str,
        amount_display: str,
    ) -> bool:
        """Send a payment link to a client via Telegram with inline button."""
        text = (
            f"\u041e\u043f\u043b\u0430\u0442\u0430 \u0437\u0430 \u0443\u0441\u043b\u0443\u0433\u0443 <b>{service_name}</b>\n"
            f"\u0421\u0443\u043c\u043c\u0430: <b>{amount_display}</b>\n\n"
            f"\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u043a\u043d\u043e\u043f\u043a\u0443 \u043d\u0438\u0436\u0435 \u0434\u043b\u044f \u043e\u043f\u043b\u0430\u0442\u044b \u0447\u0435\u0440\u0435\u0437 \u0421\u0411\u041f:"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="\u041e\u043f\u043b\u0430\u0442\u0438\u0442\u044c",
                        url=payment_url,
                    )
                ]
            ]
        )
        try:
            await self._bot.send_message(
                chat_id=platform_user_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            return True
        except Exception:
            logger.exception(
                "Failed to send payment link to %s", platform_user_id
            )
            return False

    async def send_payment_requisites(
        self,
        platform_user_id: str,
        card_number: str | None,
        sbp_phone: str | None,
        bank_name: str | None,
        service_name: str,
        amount_display: str,
    ) -> bool:
        """Send payment requisites to a client via Telegram."""
        text = (
            f"\u0420\u0435\u043a\u0432\u0438\u0437\u0438\u0442\u044b \u0434\u043b\u044f \u043e\u043f\u043b\u0430\u0442\u044b:\n\n"
            f"\u0423\u0441\u043b\u0443\u0433\u0430: <b>{service_name}</b>\n"
            f"\u0421\u0443\u043c\u043c\u0430: <b>{amount_display}</b>\n\n"
        )
        if card_number:
            text += f"\u041a\u0430\u0440\u0442\u0430: <code>{card_number}</code>\n"
        if sbp_phone:
            text += f"\u0422\u0435\u043b\u0435\u0444\u043e\u043d \u0434\u043b\u044f \u0421\u0411\u041f: <code>{sbp_phone}</code>\n"
        if bank_name:
            text += f"\u0411\u0430\u043d\u043a: {bank_name}\n"
        text += f"\n\u041f\u0435\u0440\u0435\u0432\u0435\u0434\u0438\u0442\u0435 \u0443\u043a\u0430\u0437\u0430\u043d\u043d\u0443\u044e \u0441\u0443\u043c\u043c\u0443 \u0438 \u0441\u043e\u043e\u0431\u0449\u0438\u0442\u0435 \u043c\u0430\u0441\u0442\u0435\u0440\u0443."

        try:
            await self._bot.send_message(
                chat_id=platform_user_id,
                text=text,
                parse_mode="HTML",
            )
            return True
        except Exception:
            logger.exception(
                "Failed to send payment requisites to %s", platform_user_id
            )
            return False

    async def send_reminder(
        self,
        platform_user_id: str,
        service_name: str,
        booking_date: str,
        booking_time: str,
        master_name: str,
        address_note: str | None,
        booking_id: str,
        reminder_type: str,
    ) -> bool:
        """Send a booking reminder to a client via Telegram."""
        if reminder_type == "reminder_1":
            text = (
                f"\u23f0 <b>\u041d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u0435</b>\n\n"
                f"\u041d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u0435\u043c: <b>{service_name}</b> "
                f"\u0437\u0430\u0432\u0442\u0440\u0430 \u0432 {booking_time} "
                f"\u0443 \u043c\u0430\u0441\u0442\u0435\u0440\u0430 {master_name}."
            )
        else:
            text = (
                f"\u23f0 <b>\u041d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u0435</b>\n\n"
                f"\u0427\u0435\u0440\u0435\u0437 {reminder_type}: <b>{service_name}</b> "
                f"\u0432 {booking_time} "
                f"\u0443 \u043c\u0430\u0441\u0442\u0435\u0440\u0430 {master_name}."
            )

        if address_note:
            text += f"\n\U0001f4cd \u0410\u0434\u0440\u0435\u0441: {address_note}"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="\u274c \u041e\u0442\u043c\u0435\u043d\u0438\u0442\u044c \u0437\u0430\u043f\u0438\u0441\u044c",
                        callback_data=f"cancel_client:{booking_id}",
                    )
                ]
            ]
        )

        try:
            await self._bot.send_message(
                chat_id=platform_user_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            return True
        except Exception:
            logger.exception(
                "Failed to send reminder to %s", platform_user_id
            )
            return False

    async def send_booking_confirmation(
        self,
        platform_user_id: str,
        service_name: str,
        booking_date: str,
        booking_time: str,
        master_name: str,
        address_note: str | None,
        booking_id: str,
        master_id: str,
    ) -> bool:
        """Send a booking confirmation to a client via Telegram."""
        text = (
            f"\u2705 <b>\u0412\u044b \u0437\u0430\u043f\u0438\u0441\u0430\u043d\u044b!</b>\n\n"
            f"\U0001f487 <b>{service_name}</b>\n"
            f"\U0001f4c5 {booking_date} \u0432 {booking_time}\n"
            f"\U0001f464 \u041c\u0430\u0441\u0442\u0435\u0440: {master_name}"
        )

        if address_note:
            text += f"\n\U0001f4cd \u0410\u0434\u0440\u0435\u0441: {address_note}"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="\u274c \u041e\u0442\u043c\u0435\u043d\u0438\u0442\u044c \u0437\u0430\u043f\u0438\u0441\u044c",
                        callback_data=f"cancel_client:{booking_id}",
                    ),
                    InlineKeyboardButton(
                        text="\U0001f4cb \u041c\u043e\u0438 \u0437\u0430\u043f\u0438\u0441\u0438",
                        callback_data=f"my_bookings:{master_id}",
                    ),
                ]
            ]
        )

        try:
            await self._bot.send_message(
                chat_id=platform_user_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            return True
        except Exception:
            logger.exception(
                "Failed to send booking confirmation to %s", platform_user_id
            )
            return False

    async def send_review_request(
        self,
        platform_user_id: str,
        master_name: str,
        service_name: str,
        booking_id: str,
    ) -> bool:
        """Send a review request with star rating buttons via Telegram."""
        text = (
            f"\u2728 <b>\u0421\u043f\u0430\u0441\u0438\u0431\u043e \u0437\u0430 \u0432\u0438\u0437\u0438\u0442!</b>\n\n"
            f"\u041a\u0430\u043a \u0432\u0430\u043c \u0443\u0441\u043b\u0443\u0433\u0430 <b>{service_name}</b> "
            f"\u0443 \u043c\u0430\u0441\u0442\u0435\u0440\u0430 {master_name}?\n\n"
            f"\u041e\u0446\u0435\u043d\u0438\u0442\u0435 \u043e\u0442 1 \u0434\u043e 5:"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"{n}\u2b50",
                        callback_data=f"review_star:{booking_id}:{n}",
                    )
                    for n in range(1, 6)
                ]
            ]
        )
        try:
            await self._bot.send_message(
                chat_id=platform_user_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            return True
        except Exception:
            logger.exception(
                "Failed to send review request to %s", platform_user_id
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
