"""NotificationService: routes notifications to the correct platform adapter.

Singleton pattern -- import `notification_service` from this module.
"""

import logging

from app.bots.common.adapter import BookingNotification, MessengerAdapter

logger = logging.getLogger(__name__)


class NotificationService:
    """Routes booking notifications to registered platform adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, MessengerAdapter] = {}

    def register_adapter(self, platform: str, adapter: MessengerAdapter) -> None:
        """Register a messenger adapter for a platform (e.g., 'telegram')."""
        self._adapters[platform] = adapter
        logger.info("Registered %s adapter for notifications", platform)

    async def send_booking_notification(
        self, platform: str, notif: BookingNotification
    ) -> bool:
        """Send a booking notification via the appropriate platform adapter.

        Returns False if the platform has no registered adapter.
        Logs and swallows exceptions to prevent notification failures
        from breaking the booking flow.
        """
        adapter = self._adapters.get(platform)
        if not adapter:
            logger.warning(
                "No adapter registered for platform '%s'", platform
            )
            return False
        try:
            return await adapter.send_booking_notification(notif)
        except Exception:
            logger.exception(
                "Failed to send %s notification via %s",
                notif.notification_type,
                platform,
            )
            return False

    async def send_message(
        self,
        platform: str,
        platform_user_id: str,
        text: str,
    ) -> bool:
        """Send a plain text message via the appropriate platform adapter."""
        adapter = self._adapters.get(platform)
        if not adapter:
            logger.warning(
                "No adapter registered for platform '%s'", platform
            )
            return False
        try:
            return await adapter.send_message(
                platform_user_id=platform_user_id,
                text=text,
            )
        except Exception:
            logger.exception(
                "Failed to send message via %s", platform
            )
            return False

    async def send_payment_link(
        self,
        platform: str,
        platform_user_id: str,
        payment_url: str,
        service_name: str,
        amount_display: str,
    ) -> bool:
        """Send a payment link to a client via the appropriate platform adapter."""
        adapter = self._adapters.get(platform)
        if not adapter:
            logger.warning(
                "No adapter registered for platform '%s'", platform
            )
            return False
        try:
            return await adapter.send_payment_link(
                platform_user_id=platform_user_id,
                payment_url=payment_url,
                service_name=service_name,
                amount_display=amount_display,
            )
        except Exception:
            logger.exception(
                "Failed to send payment link via %s", platform
            )
            return False

    async def send_payment_requisites(
        self,
        platform: str,
        platform_user_id: str,
        card_number: str | None,
        sbp_phone: str | None,
        bank_name: str | None,
        service_name: str,
        amount_display: str,
    ) -> bool:
        """Send payment requisites to a client via the appropriate platform adapter."""
        adapter = self._adapters.get(platform)
        if not adapter:
            logger.warning(
                "No adapter registered for platform '%s'", platform
            )
            return False
        try:
            return await adapter.send_payment_requisites(
                platform_user_id=platform_user_id,
                card_number=card_number,
                sbp_phone=sbp_phone,
                bank_name=bank_name,
                service_name=service_name,
                amount_display=amount_display,
            )
        except Exception:
            logger.exception(
                "Failed to send payment requisites via %s", platform
            )
            return False

    async def send_reminder(
        self,
        platform: str,
        platform_user_id: str,
        service_name: str,
        booking_date: str,
        booking_time: str,
        master_name: str,
        address_note: str | None,
        booking_id: str,
        reminder_type: str,
    ) -> bool:
        """Send a booking reminder to a client via the appropriate platform adapter."""
        adapter = self._adapters.get(platform)
        if not adapter:
            logger.warning(
                "No adapter registered for platform '%s'", platform
            )
            return False
        try:
            return await adapter.send_reminder(
                platform_user_id=platform_user_id,
                service_name=service_name,
                booking_date=booking_date,
                booking_time=booking_time,
                master_name=master_name,
                address_note=address_note,
                booking_id=booking_id,
                reminder_type=reminder_type,
            )
        except Exception:
            logger.exception(
                "Failed to send reminder via %s", platform
            )
            return False

    async def send_receipt_link(
        self,
        platform: str,
        platform_user_id: str,
        receipt_url: str,
        service_name: str,
    ) -> bool:
        """Send a receipt link to a client via the appropriate platform adapter.

        Convenience wrapper around send_message with formatted receipt text.
        """
        text = f'Чек по услуге "{service_name}":\n{receipt_url}'
        return await self.send_message(
            platform=platform,
            platform_user_id=platform_user_id,
            text=text,
        )

    async def send_booking_confirmation(
        self,
        platform: str,
        platform_user_id: str,
        service_name: str,
        booking_date: str,
        booking_time: str,
        master_name: str,
        address_note: str | None,
        booking_id: str,
        master_id: str,
    ) -> bool:
        """Send a booking confirmation to a client via the appropriate platform adapter."""
        adapter = self._adapters.get(platform)
        if not adapter:
            logger.warning(
                "No adapter registered for platform '%s'", platform
            )
            return False
        try:
            return await adapter.send_booking_confirmation(
                platform_user_id=platform_user_id,
                service_name=service_name,
                booking_date=booking_date,
                booking_time=booking_time,
                master_name=master_name,
                address_note=address_note,
                booking_id=booking_id,
                master_id=master_id,
            )
        except Exception:
            logger.exception(
                "Failed to send booking confirmation via %s", platform
            )
            return False


# Module-level singleton
notification_service = NotificationService()
