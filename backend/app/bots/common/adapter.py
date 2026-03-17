"""MessengerAdapter ABC and BookingNotification dataclass.

Defines the platform-agnostic interface for sending notifications.
Each messenger (Telegram, MAX, VK) implements this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BookingNotification:
    """Platform-agnostic booking notification payload."""

    master_platform_id: str  # TG user_id, VK user_id, etc.
    client_name: str
    service_name: str
    booking_time: str  # Formatted: "14:00"
    booking_date: str  # Formatted: "25.03.2026"
    booking_id: str
    notification_type: str  # "new", "cancelled", "rescheduled"
    price: int | None = None  # in kopecks


class MessengerAdapter(ABC):
    """Abstract base class for messenger platform adapters."""

    @abstractmethod
    async def send_booking_notification(
        self, notif: BookingNotification
    ) -> bool:
        """Send a booking notification to a master. Returns True on success."""
        ...

    @abstractmethod
    async def send_message(
        self, platform_user_id: str, text: str
    ) -> bool:
        """Send a plain text message to a user. Returns True on success."""
        ...
