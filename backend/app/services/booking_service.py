"""Booking service: create, cancel, reschedule with double-booking prevention."""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking
from app.models.client import Client, ClientPlatform
from app.models.master import Master
from app.models.service import Service
from app.services.client_service import (
    find_or_create_client,
    get_or_create_master_client,
    update_visit_stats,
)

logger = logging.getLogger(__name__)


async def _notify_master(
    db: AsyncSession,
    booking: Booking,
    notification_type: str,
) -> None:
    """Send a booking notification to the master via their registered platform.

    Fire-and-forget: logs errors but never raises.
    """
    try:
        from app.bots.common.adapter import BookingNotification
        from app.bots.common.notification import notification_service

        # Load master to get platform user IDs
        result = await db.execute(
            select(Master).where(Master.id == booking.master_id)
        )
        master = result.scalar_one_or_none()
        if not master:
            return

        # Collect all platforms master is registered on
        platform_ids: list[tuple[str, str]] = []
        if master.tg_user_id:
            platform_ids.append(("telegram", master.tg_user_id))
        if master.max_user_id:
            platform_ids.append(("max", master.max_user_id))
        if master.vk_user_id:
            platform_ids.append(("vk", master.vk_user_id))

        if not platform_ids:
            return

        # Load related objects if not already loaded
        if not booking.service:
            svc_result = await db.execute(
                select(Service).where(Service.id == booking.service_id)
            )
            service = svc_result.scalar_one_or_none()
        else:
            service = booking.service

        from app.models.client import Client

        if not booking.client:
            client_result = await db.execute(
                select(Client).where(Client.id == booking.client_id)
            )
            client = client_result.scalar_one_or_none()
        else:
            client = booking.client

        client_name = client.name if client else "Client"
        service_name = service.name if service else "Service"
        service_price = service.price if service else None

        # Send notification to all registered platforms
        for platform, platform_id in platform_ids:
            notif = BookingNotification(
                master_platform_id=platform_id,
                client_name=client_name,
                service_name=service_name,
                booking_time=booking.starts_at.strftime("%H:%M"),
                booking_date=booking.starts_at.strftime("%d.%m.%Y"),
                booking_id=str(booking.id),
                notification_type=notification_type,
                price=service_price,
            )

            await notification_service.send_booking_notification(
                platform, notif
            )
    except Exception:
        logger.exception(
            "Failed to send %s notification for booking %s",
            notification_type,
            booking.id,
        )


async def _notify_client_confirmation(
    db: AsyncSession,
    booking: Booking,
) -> None:
    """Send a booking confirmation to the client via their platform.

    Fire-and-forget: logs errors but never raises.
    """
    try:
        from app.bots.common.notification import notification_service

        # Load client + platforms
        result = await db.execute(
            select(Client)
            .where(Client.id == booking.client_id)
            .options(selectinload(Client.platforms))
        )
        client = result.scalar_one_or_none()
        if not client:
            return

        # Find platform matching source_platform
        platform_record = None
        for p in client.platforms:
            if p.platform == booking.source_platform:
                platform_record = p
                break

        if not platform_record:
            return

        # Load master for name + address_note
        master_result = await db.execute(
            select(Master).where(Master.id == booking.master_id)
        )
        master = master_result.scalar_one_or_none()
        if not master:
            return

        # Load service for name
        svc_result = await db.execute(
            select(Service).where(Service.id == booking.service_id)
        )
        service = svc_result.scalar_one_or_none()

        # Convert to master's local timezone for display
        tz = ZoneInfo(master.timezone)
        local_start = booking.starts_at.astimezone(tz)

        await notification_service.send_booking_confirmation(
            platform=booking.source_platform,
            platform_user_id=platform_record.platform_user_id,
            service_name=service.name if service else "Service",
            booking_date=local_start.strftime("%d.%m.%Y"),
            booking_time=local_start.strftime("%H:%M"),
            master_name=master.name,
            address_note=master.address_note,
            booking_id=str(booking.id),
            master_id=str(master.id),
        )
    except Exception:
        logger.exception(
            "Failed to send confirmation for booking %s", booking.id
        )


async def _notify_client_change(
    db: AsyncSession,
    booking: Booking,
    change_type: str,
) -> None:
    """Notify client about booking cancellation or reschedule.

    Fire-and-forget: logs errors but never raises.
    change_type: "cancelled" or "rescheduled"
    """
    try:
        from app.bots.common.notification import notification_service

        # Load client + platforms
        result = await db.execute(
            select(Client)
            .where(Client.id == booking.client_id)
            .options(selectinload(Client.platforms))
        )
        client = result.scalar_one_or_none()
        if not client:
            return

        # Find platform matching source_platform
        platform_record = None
        source = booking.source_platform or "telegram"
        for p in client.platforms:
            if p.platform == source:
                platform_record = p
                break

        if not platform_record:
            return

        # Load master for name + timezone
        master_result = await db.execute(
            select(Master).where(Master.id == booking.master_id)
        )
        master = master_result.scalar_one_or_none()
        if not master:
            return

        # Load service for name
        svc_result = await db.execute(
            select(Service).where(Service.id == booking.service_id)
        )
        service = svc_result.scalar_one_or_none()

        tz = ZoneInfo(master.timezone)
        local_start = booking.starts_at.astimezone(tz)
        service_name = service.name if service else "Service"
        date_str = local_start.strftime("%d.%m.%Y")
        time_str = local_start.strftime("%H:%M")

        if change_type == "cancelled":
            text = (
                f"\u274c <b>\u0417\u0430\u043f\u0438\u0441\u044c \u043e\u0442\u043c\u0435\u043d\u0435\u043d\u0430</b>\n\n"
                f"\U0001f487 {service_name}\n"
                f"\U0001f4c5 {date_str} \u0432 {time_str}\n"
                f"\u0443 \u043c\u0430\u0441\u0442\u0435\u0440\u0430 {master.name}"
            )
        else:  # rescheduled
            text = (
                f"\U0001f504 <b>\u0417\u0430\u043f\u0438\u0441\u044c \u043f\u0435\u0440\u0435\u043d\u0435\u0441\u0435\u043d\u0430</b>\n\n"
                f"\U0001f487 {service_name}\n"
                f"\U0001f4c5 \u041d\u043e\u0432\u043e\u0435 \u0432\u0440\u0435\u043c\u044f: {date_str} \u0432 {time_str}\n"
                f"\u0443 \u043c\u0430\u0441\u0442\u0435\u0440\u0430 {master.name}"
            )

        await notification_service.send_message(
            platform=source,
            platform_user_id=platform_record.platform_user_id,
            text=text,
        )
    except Exception:
        logger.exception(
            "Failed to send %s notification to client for booking %s",
            change_type,
            booking.id,
        )


async def create_booking(
    db: AsyncSession,
    master_id: uuid.UUID,
    service_id: uuid.UUID,
    starts_at: datetime,
    client_name: str,
    client_phone: str,
    source_platform: str = "telegram",
    platform_user_id: str | None = None,
) -> Booking:
    """
    Create a booking with double-booking prevention.

    1. Verify service exists and belongs to master
    2. Calculate ends_at from service duration
    3. SELECT FOR UPDATE to check for overlapping bookings
    4. Find or create client
    5. Create booking + update visit stats
    6. Send notification to master
    """
    # 1. Load service
    svc_result = await db.execute(
        select(Service).where(
            and_(
                Service.id == service_id,
                Service.master_id == master_id,
                Service.is_active.is_(True),
            )
        )
    )
    service = svc_result.scalar_one_or_none()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    # 2. Calculate ends_at
    ends_at = starts_at + timedelta(minutes=service.duration_minutes)

    # 3. SELECT FOR UPDATE: check for overlapping confirmed/pending bookings
    overlap_result = await db.execute(
        select(Booking)
        .where(
            and_(
                Booking.master_id == master_id,
                Booking.status.in_(["confirmed", "pending"]),
                Booking.starts_at < ends_at,
                Booking.ends_at > starts_at,
            )
        )
        .with_for_update()
    )
    conflicting = overlap_result.scalar_one_or_none()
    if conflicting is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This time slot is no longer available",
        )

    # 4. Find or create client
    client = await find_or_create_client(
        db=db,
        name=client_name,
        phone=client_phone,
        platform=source_platform,
        platform_user_id=platform_user_id,
    )

    # 5. Create MasterClient link + update visit stats
    master_client = await get_or_create_master_client(db, master_id, client.id)

    booking = Booking(
        master_id=master_id,
        client_id=client.id,
        service_id=service_id,
        starts_at=starts_at,
        ends_at=ends_at,
        status="confirmed",
        source_platform=source_platform,
    )
    db.add(booking)

    await update_visit_stats(db, master_client, starts_at)

    # flush to trigger exclusion constraint check
    await db.flush()
    await db.refresh(booking)

    # 6. Send notification to master (fire-and-forget)
    await _notify_master(db, booking, "new")

    # 7. Send booking confirmation to client (fire-and-forget)
    await _notify_client_confirmation(db, booking)

    return booking


async def cancel_booking(
    db: AsyncSession,
    booking_id: uuid.UUID,
    cancelled_by: str,
    master_id: uuid.UUID | None = None,
    cancellation_deadline_hours: int | None = None,
) -> Booking:
    """
    Cancel a booking.

    cancelled_by: "client" or "master"
    If cancelled_by == "client" and deadline is set, enforce it.
    """
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    if cancelled_by == "client" and cancellation_deadline_hours is not None:
        now = datetime.now(timezone.utc)
        deadline = booking.starts_at - timedelta(hours=cancellation_deadline_hours)
        if now > deadline:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cancellation deadline passed. Must cancel at least {cancellation_deadline_hours}h before appointment.",
            )

    booking.status = (
        "cancelled_by_client" if cancelled_by == "client" else "cancelled_by_master"
    )
    await db.flush()
    await db.refresh(booking)

    # Clean up pending reminders (fire-and-forget)
    try:
        from app.services.reminder_service import cleanup_reminders_for_booking
        await cleanup_reminders_for_booking(db, booking_id)
    except Exception:
        logger.exception("Failed to cleanup reminders for booking %s", booking_id)

    # Send cancellation notification to master (fire-and-forget)
    await _notify_master(db, booking, "cancelled")

    # Notify client about cancellation (fire-and-forget)
    await _notify_client_change(db, booking, "cancelled")

    return booking


async def reschedule_booking(
    db: AsyncSession,
    booking_id: uuid.UUID,
    new_starts_at: datetime,
    rescheduled_by: str,
    master_id: uuid.UUID | None = None,
    cancellation_deadline_hours: int | None = None,
) -> Booking:
    """
    Reschedule a booking to a new time.

    Same deadline check as cancel for client reschedule.
    Checks for slot conflicts at the new time.
    """
    result = await db.execute(
        select(Booking)
        .where(Booking.id == booking_id)
        .options(selectinload(Booking.service))
    )
    booking = result.scalar_one_or_none()
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Deadline check for client reschedule
    if rescheduled_by == "client" and cancellation_deadline_hours is not None:
        now = datetime.now(timezone.utc)
        deadline = booking.starts_at - timedelta(hours=cancellation_deadline_hours)
        if now > deadline:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Reschedule deadline passed. Must reschedule at least {cancellation_deadline_hours}h before appointment.",
            )

    # Calculate new ends_at from service duration
    service = booking.service
    new_ends_at = new_starts_at + timedelta(minutes=service.duration_minutes)

    # Check for conflicts at the new time (excluding current booking)
    overlap_result = await db.execute(
        select(Booking)
        .where(
            and_(
                Booking.master_id == booking.master_id,
                Booking.id != booking_id,
                Booking.status.in_(["confirmed", "pending"]),
                Booking.starts_at < new_ends_at,
                Booking.ends_at > new_starts_at,
            )
        )
        .with_for_update()
    )
    conflicting = overlap_result.scalar_one_or_none()
    if conflicting is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This time slot is no longer available",
        )

    booking.starts_at = new_starts_at
    booking.ends_at = new_ends_at
    await db.flush()
    await db.refresh(booking)

    # Clean up pending reminders so fresh ones get sent for the new time
    try:
        from app.services.reminder_service import cleanup_reminders_for_booking
        await cleanup_reminders_for_booking(db, booking_id)
    except Exception:
        logger.exception("Failed to cleanup reminders for booking %s", booking_id)

    # Send reschedule notification to master (fire-and-forget)
    await _notify_master(db, booking, "rescheduled")

    # Notify client about reschedule (fire-and-forget)
    await _notify_client_change(db, booking, "rescheduled")

    return booking


async def create_manual_booking(
    db: AsyncSession,
    master_id: uuid.UUID,
    service_id: uuid.UUID,
    starts_at: datetime,
    client_name: str,
    client_phone: str,
    notes: str | None = None,
) -> Booking:
    """Create a booking manually by the master (source_platform='web')."""
    booking = await create_booking(
        db=db,
        master_id=master_id,
        service_id=service_id,
        starts_at=starts_at,
        client_name=client_name,
        client_phone=client_phone,
        source_platform="web",
    )
    if notes:
        booking.notes = notes
        await db.flush()
        await db.refresh(booking)
    return booking


async def get_master_bookings(
    db: AsyncSession,
    master_id: uuid.UUID,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    booking_status: str | None = None,
) -> list[Booking]:
    """List bookings for a master with optional filters. Eager-loads client and service."""
    stmt = (
        select(Booking)
        .where(Booking.master_id == master_id)
        .options(selectinload(Booking.client), selectinload(Booking.service))
        .order_by(Booking.starts_at.desc())
    )

    if date_from is not None:
        stmt = stmt.where(Booking.starts_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(Booking.starts_at <= date_to)
    if booking_status is not None:
        stmt = stmt.where(Booking.status == booking_status)

    result = await db.execute(stmt)
    return list(result.scalars().all())
