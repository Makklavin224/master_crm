"""Reminder service: APScheduler-based polling for upcoming bookings.

Polls every 5 minutes, sends due reminders via NotificationService,
tracks sent reminders in scheduled_reminders for idempotency.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bots.common.notification import notification_service
from app.core.database import async_session_factory
from app.models.booking import Booking
from app.models.client import Client, ClientPlatform
from app.models.master import Master
from app.models.scheduled_reminder import ScheduledReminder
from app.models.service import Service

logger = logging.getLogger(__name__)

# Module-level scheduler singleton
scheduler = AsyncIOScheduler(timezone="UTC")


async def process_pending_reminders() -> None:
    """Poll for upcoming bookings and send due reminders.

    For each master with reminders_enabled=True:
    1. Query confirmed bookings in the reminder window
    2. Check if reminder_1 or reminder_2 is due
    3. Send if not already sent (idempotent via scheduled_reminders table)
    """
    try:
        async with async_session_factory() as session:
            now = datetime.now(timezone.utc)

            # Get all masters with reminders enabled
            masters_result = await session.execute(
                select(Master).where(Master.reminders_enabled.is_(True))
            )
            masters = masters_result.scalars().all()

            for master in masters:
                try:
                    await _process_master_reminders(session, master, now)
                except Exception:
                    logger.exception(
                        "Error processing reminders for master %s",
                        master.id,
                    )

            await session.commit()

    except Exception:
        logger.exception("Error in process_pending_reminders")


async def _process_master_reminders(
    session: AsyncSession,
    master: Master,
    now: datetime,
) -> None:
    """Process reminders for a single master."""
    # Calculate the maximum look-ahead window
    max_hours = master.reminder_1_hours
    if master.reminder_2_hours is not None:
        max_hours = max(max_hours, master.reminder_2_hours)

    upper_bound = now + timedelta(hours=max_hours)

    # Query confirmed bookings in the future within the window
    bookings_result = await session.execute(
        select(Booking)
        .where(
            and_(
                Booking.master_id == master.id,
                Booking.status == "confirmed",
                Booking.starts_at > now,
                Booking.starts_at <= upper_bound,
            )
        )
    )
    bookings = bookings_result.scalars().all()

    for booking in bookings:
        await _process_booking_reminders(session, master, booking, now)


async def _process_booking_reminders(
    session: AsyncSession,
    master: Master,
    booking: Booking,
    now: datetime,
) -> None:
    """Check and send reminders for a single booking."""
    # Check reminder_1
    reminder_1_threshold = booking.starts_at - timedelta(hours=master.reminder_1_hours)
    if reminder_1_threshold <= now:
        await _maybe_send_reminder(
            session, master, booking, "reminder_1", now
        )

    # Check reminder_2 (skip if disabled)
    if master.reminder_2_hours is not None:
        reminder_2_threshold = booking.starts_at - timedelta(hours=master.reminder_2_hours)
        if reminder_2_threshold <= now:
            await _maybe_send_reminder(
                session, master, booking, "reminder_2", now
            )


async def _maybe_send_reminder(
    session: AsyncSession,
    master: Master,
    booking: Booking,
    reminder_type: str,
    now: datetime,
) -> None:
    """Send a reminder if not already sent (idempotency check)."""
    # Check if already sent or pending
    existing_result = await session.execute(
        select(ScheduledReminder).where(
            and_(
                ScheduledReminder.booking_id == booking.id,
                ScheduledReminder.reminder_type == reminder_type,
                ScheduledReminder.status.in_(["sent", "pending"]),
            )
        )
    )
    if existing_result.scalar_one_or_none() is not None:
        return  # Already handled

    # Find client's platform for sending
    client_result = await session.execute(
        select(Client).where(Client.id == booking.client_id)
    )
    client = client_result.scalar_one_or_none()
    if not client:
        return

    # Get platform record matching booking source
    source_platform = booking.source_platform or "telegram"
    platform_result = await session.execute(
        select(ClientPlatform).where(
            and_(
                ClientPlatform.client_id == client.id,
                ClientPlatform.platform == source_platform,
            )
        )
    )
    platform_record = platform_result.scalar_one_or_none()
    if not platform_record:
        return

    # Load service name
    svc_result = await session.execute(
        select(Service).where(Service.id == booking.service_id)
    )
    service = svc_result.scalar_one_or_none()
    service_name = service.name if service else "Service"

    # Convert to master's local timezone for display
    tz = ZoneInfo(master.timezone)
    local_start = booking.starts_at.astimezone(tz)

    # Determine scheduled_for time
    hours = master.reminder_1_hours if reminder_type == "reminder_1" else master.reminder_2_hours
    scheduled_for = booking.starts_at - timedelta(hours=hours)

    # Send the reminder
    try:
        success = await notification_service.send_reminder(
            platform=source_platform,
            platform_user_id=platform_record.platform_user_id,
            service_name=service_name,
            booking_date=local_start.strftime("%d.%m.%Y"),
            booking_time=local_start.strftime("%H:%M"),
            master_name=master.name,
            address_note=master.address_note,
            booking_id=str(booking.id),
            reminder_type=reminder_type,
        )

        # Record the result
        reminder_record = ScheduledReminder(
            booking_id=booking.id,
            master_id=master.id,
            reminder_type=reminder_type,
            scheduled_for=scheduled_for,
            sent_at=now if success else None,
            status="sent" if success else "failed",
            error_message=None if success else "send_reminder returned False",
        )
        session.add(reminder_record)
        await session.flush()

        if success:
            logger.info(
                "Sent %s for booking %s to client %s",
                reminder_type,
                booking.id,
                client.id,
            )
        else:
            logger.warning(
                "Failed to send %s for booking %s",
                reminder_type,
                booking.id,
            )

    except Exception as e:
        logger.exception(
            "Error sending %s for booking %s",
            reminder_type,
            booking.id,
        )
        # Record the failure
        reminder_record = ScheduledReminder(
            booking_id=booking.id,
            master_id=master.id,
            reminder_type=reminder_type,
            scheduled_for=scheduled_for,
            status="failed",
            error_message=str(e)[:500],
        )
        session.add(reminder_record)
        await session.flush()


async def cleanup_reminders_for_booking(
    db: AsyncSession,
    booking_id: uuid.UUID,
) -> None:
    """Delete pending reminders for a booking (called on cancel/reschedule)."""
    await db.execute(
        delete(ScheduledReminder).where(
            and_(
                ScheduledReminder.booking_id == booking_id,
                ScheduledReminder.status == "pending",
            )
        )
    )


# Register the polling job
scheduler.add_job(
    process_pending_reminders,
    "interval",
    minutes=5,
    id="reminder_poll",
    replace_existing=True,
    misfire_grace_time=300,
)

# Register receipt retry polling job
from app.services.receipt_service import process_pending_receipts  # noqa: E402

scheduler.add_job(
    process_pending_receipts,
    "interval",
    minutes=5,
    id="receipt_retry_poll",
    replace_existing=True,
    misfire_grace_time=300,
)
