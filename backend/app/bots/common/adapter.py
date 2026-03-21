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

    @abstractmethod
    async def send_payment_link(
        self,
        platform_user_id: str,
        payment_url: str,
        service_name: str,
        amount_display: str,
    ) -> bool:
        """Send a payment link to a client. Returns True on success."""
        ...

    @abstractmethod
    async def send_payment_requisites(
        self,
        platform_user_id: str,
        card_number: str | None,
        sbp_phone: str | None,
        bank_name: str | None,
        service_name: str,
        amount_display: str,
    ) -> bool:
        """Send payment requisites to a client. Returns True on success."""
        ...

    @abstractmethod
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
        """Send a booking reminder to a client. Returns True on success."""
        ...

    @abstractmethod
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
        """Send a booking confirmation to a client. Returns True on success."""
        ...

    @abstractmethod
    async def send_review_request(
        self,
        platform_user_id: str,
        master_name: str,
        service_name: str,
        booking_id: str,
    ) -> bool:
        """Send a review request with star rating buttons to a client."""
        ...
