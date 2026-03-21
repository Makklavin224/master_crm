"""VkAdapter: implements MessengerAdapter for the VK platform.

Uses httpx.AsyncClient to call VK API for sending messages
with plain text (VK messages.send does not support HTML).
Inline keyboards use VK JSON format with callback/open_link actions.
"""

import json
import logging

import httpx

from app.bots.common.adapter import BookingNotification, MessengerAdapter

logger = logging.getLogger(__name__)

VK_API_URL = "https://api.vk.com/method/"
VK_API_VERSION = "5.199"


class VkAdapter(MessengerAdapter):
    """Sends booking notifications and messages via VK community bot."""

    def __init__(self, group_token: str) -> None:
        self._token = group_token

    async def _send(
        self,
        user_id: str,
        message: str,
        keyboard: dict | None = None,
    ) -> bool:
        """Send a message via VK API messages.send.

        Returns True on success, False on error.
        """
        data: dict = {
            "user_id": int(user_id),
            "message": message,
            "random_id": 0,
            "access_token": self._token,
            "v": VK_API_VERSION,
        }
        if keyboard:
            data["keyboard"] = json.dumps(keyboard)

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{VK_API_URL}messages.send",
                    data=data,
                )
                result = resp.json()
                if "error" in result:
                    logger.error(
                        "VK API error sending to %s: %s",
                        user_id,
                        result["error"],
                    )
                    return False
                return True
        except Exception:
            logger.exception("Failed to send VK message to %s", user_id)
            return False

    async def send_booking_notification(
        self, notif: BookingNotification
    ) -> bool:
        """Format and send a booking notification to a master via VK."""
        text = self._format_notification(notif)
        keyboard = self._build_keyboard(notif)
        return await self._send(notif.master_platform_id, text, keyboard)

    async def send_message(
        self, platform_user_id: str, text: str
    ) -> bool:
        """Send a simple text message via VK."""
        return await self._send(platform_user_id, text)

    async def send_payment_link(
        self,
        platform_user_id: str,
        payment_url: str,
        service_name: str,
        amount_display: str,
    ) -> bool:
        """Send a payment link to a client via VK with inline button."""
        text = (
            f"\u041e\u043f\u043b\u0430\u0442\u0430 \u0437\u0430 \u0443\u0441\u043b\u0443\u0433\u0443 {service_name}\n"
            f"\u0421\u0443\u043c\u043c\u0430: {amount_display}\n\n"
            f"\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u043a\u043d\u043e\u043f\u043a\u0443 \u043d\u0438\u0436\u0435 \u0434\u043b\u044f \u043e\u043f\u043b\u0430\u0442\u044b \u0447\u0435\u0440\u0435\u0437 \u0421\u0411\u041f:"
        )
        keyboard = {
            "inline": True,
            "buttons": [[
                {
                    "action": {
                        "type": "open_link",
                        "label": "\u041e\u043f\u043b\u0430\u0442\u0438\u0442\u044c",
                        "link": payment_url,
                    }
                }
            ]],
        }
        return await self._send(platform_user_id, text, keyboard)

    async def send_payment_requisites(
        self,
        platform_user_id: str,
        card_number: str | None,
        sbp_phone: str | None,
        bank_name: str | None,
        service_name: str,
        amount_display: str,
    ) -> bool:
        """Send payment requisites to a client via VK."""
        text = (
            f"\u0420\u0435\u043a\u0432\u0438\u0437\u0438\u0442\u044b \u0434\u043b\u044f \u043e\u043f\u043b\u0430\u0442\u044b:\n\n"
            f"\u0423\u0441\u043b\u0443\u0433\u0430: {service_name}\n"
            f"\u0421\u0443\u043c\u043c\u0430: {amount_display}\n\n"
        )
        if card_number:
            text += f"\u041a\u0430\u0440\u0442\u0430: {card_number}\n"
        if sbp_phone:
            text += f"\u0422\u0435\u043b\u0435\u0444\u043e\u043d \u0434\u043b\u044f \u0421\u0411\u041f: {sbp_phone}\n"
        if bank_name:
            text += f"\u0411\u0430\u043d\u043a: {bank_name}\n"
        text += f"\n\u041f\u0435\u0440\u0435\u0432\u0435\u0434\u0438\u0442\u0435 \u0443\u043a\u0430\u0437\u0430\u043d\u043d\u0443\u044e \u0441\u0443\u043c\u043c\u0443 \u0438 \u0441\u043e\u043e\u0431\u0449\u0438\u0442\u0435 \u043c\u0430\u0441\u0442\u0435\u0440\u0443."
        return await self._send(platform_user_id, text)

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
        """Send a booking reminder to a client via VK."""
        if reminder_type == "reminder_1":
            text = (
                f"\u23f0 \u041d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u0435\n\n"
                f"\u041d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u0435\u043c: {service_name} "
                f"\u0437\u0430\u0432\u0442\u0440\u0430 \u0432 {booking_time} "
                f"\u0443 \u043c\u0430\u0441\u0442\u0435\u0440\u0430 {master_name}."
            )
        else:
            text = (
                f"\u23f0 \u041d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u0435\n\n"
                f"\u0427\u0435\u0440\u0435\u0437 {reminder_type}: {service_name} "
                f"\u0432 {booking_time} "
                f"\u0443 \u043c\u0430\u0441\u0442\u0435\u0440\u0430 {master_name}."
            )

        if address_note:
            text += f"\n\U0001f4cd \u0410\u0434\u0440\u0435\u0441: {address_note}"

        keyboard = {
            "inline": True,
            "buttons": [[
                {
                    "action": {
                        "type": "callback",
                        "label": "\u274c \u041e\u0442\u043c\u0435\u043d\u0438\u0442\u044c \u0437\u0430\u043f\u0438\u0441\u044c",
                        "payload": json.dumps({"cmd": f"cancel_client:{booking_id}"}),
                    }
                }
            ]],
        }
        return await self._send(platform_user_id, text, keyboard)

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
        """Send a booking confirmation to a client via VK."""
        text = (
            f"\u2705 \u0412\u044b \u0437\u0430\u043f\u0438\u0441\u0430\u043d\u044b!\n\n"
            f"\U0001f487 {service_name}\n"
            f"\U0001f4c5 {booking_date} \u0432 {booking_time}\n"
            f"\U0001f464 \u041c\u0430\u0441\u0442\u0435\u0440: {master_name}"
        )

        if address_note:
            text += f"\n\U0001f4cd \u0410\u0434\u0440\u0435\u0441: {address_note}"

        keyboard = {
            "inline": True,
            "buttons": [[
                {
                    "action": {
                        "type": "callback",
                        "label": "\u274c \u041e\u0442\u043c\u0435\u043d\u0438\u0442\u044c \u0437\u0430\u043f\u0438\u0441\u044c",
                        "payload": json.dumps({"cmd": f"cancel_client:{booking_id}"}),
                    }
                },
                {
                    "action": {
                        "type": "callback",
                        "label": "\U0001f4cb \u041c\u043e\u0438 \u0437\u0430\u043f\u0438\u0441\u0438",
                        "payload": json.dumps({"cmd": f"my_bookings:{master_id}"}),
                    }
                },
            ]],
        }
        return await self._send(platform_user_id, text, keyboard)

    async def send_review_request(
        self,
        platform_user_id: str,
        master_name: str,
        service_name: str,
        booking_id: str,
    ) -> bool:
        """Send a review request with star rating buttons via VK."""
        text = (
            f"\u2728 \u0421\u043f\u0430\u0441\u0438\u0431\u043e \u0437\u0430 \u0432\u0438\u0437\u0438\u0442!\n\n"
            f"\u041a\u0430\u043a \u0432\u0430\u043c \u0443\u0441\u043b\u0443\u0433\u0430 {service_name} "
            f"\u0443 \u043c\u0430\u0441\u0442\u0435\u0440\u0430 {master_name}?\n\n"
            f"\u041e\u0446\u0435\u043d\u0438\u0442\u0435 \u043e\u0442 1 \u0434\u043e 5:"
        )
        keyboard = {
            "inline": True,
            "buttons": [[
                {
                    "action": {
                        "type": "callback",
                        "label": f"{n}\u2b50",
                        "payload": json.dumps({"cmd": f"review_star:{booking_id}:{n}"}),
                    }
                }
                for n in range(1, 6)
            ]],
        }
        return await self._send(platform_user_id, text, keyboard)

    @staticmethod
    def _format_notification(notif: BookingNotification) -> str:
        """Build plain text notification based on notification type (Russian).

        VK messages.send does not support HTML, so plain text with emojis is used.
        """
        if notif.notification_type == "new":
            price_line = ""
            if notif.price is not None:
                rub = notif.price // 100
                price_line = f"\n\U0001f4b0 {rub} \u20bd"
            return (
                f"\u2728 \u041d\u043e\u0432\u0430\u044f \u0437\u0430\u043f\u0438\u0441\u044c!\n\n"
                f"\U0001f464 {notif.client_name}\n"
                f"\U0001f487 {notif.service_name}\n"
                f"\U0001f4c5 {notif.booking_date}\n"
                f"\U0001f550 {notif.booking_time}"
                f"{price_line}"
            )
        elif notif.notification_type == "cancelled":
            return (
                f"\u274c \u0417\u0430\u043f\u0438\u0441\u044c \u043e\u0442\u043c\u0435\u043d\u0435\u043d\u0430\n\n"
                f"\U0001f464 {notif.client_name}\n"
                f"\U0001f4c5 {notif.booking_date} \u0432 {notif.booking_time}"
            )
        elif notif.notification_type == "rescheduled":
            return (
                f"\U0001f504 \u0417\u0430\u043f\u0438\u0441\u044c \u043f\u0435\u0440\u0435\u043d\u0435\u0441\u0435\u043d\u0430\n\n"
                f"\U0001f464 {notif.client_name}\n"
                f"\U0001f4c5 {notif.booking_date}\n"
                f"\U0001f550 {notif.booking_time}"
            )
        else:
            return (
                f"\u0417\u0430\u043f\u0438\u0441\u044c\n\n"
                f"\U0001f464 {notif.client_name}\n"
                f"\U0001f4c5 {notif.booking_date}\n"
                f"\U0001f550 {notif.booking_time}"
            )

    @staticmethod
    def _build_keyboard(notif: BookingNotification) -> dict:
        """Build VK inline keyboard with action buttons."""
        return {
            "inline": True,
            "buttons": [[
                {
                    "action": {
                        "type": "callback",
                        "label": "\U0001f4cb \u041f\u043e\u0434\u0440\u043e\u0431\u043d\u0435\u0435",
                        "payload": json.dumps({"cmd": f"booking:{notif.booking_id}"}),
                    }
                },
                {
                    "action": {
                        "type": "callback",
                        "label": "\U0001f4c5 \u0420\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435",
                        "payload": json.dumps({"cmd": "today"}),
                    }
                },
            ]],
        }
