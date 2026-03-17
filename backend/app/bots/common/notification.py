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


# Module-level singleton
notification_service = NotificationService()
