"""Tests for reminder scheduling service: polling, idempotency, cleanup."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.models.booking import Booking
from app.models.client import Client, ClientPlatform
from app.models.master import Master
from app.models.scheduled_reminder import ScheduledReminder
from app.models.service import Service


@pytest.fixture
async def reminder_setup(db_session, master_factory, service_factory, client_factory, client_platform_factory, booking_factory):
    """Create master, service, client with platform, and a confirmed booking 23h from now."""
    master = await master_factory(name="Reminder Master")
    master.tg_user_id = "master_reminder_1"
    master.reminders_enabled = True
    master.reminder_1_hours = 24
    master.reminder_2_hours = 2
    master.address_note = "ул. Ленина 5"
    master.timezone = "Europe/Moscow"
    await db_session.flush()

    svc = await service_factory(master.id, name="Haircut", duration_minutes=60)
    test_client = await client_factory(name="Reminder Client")
    platform = await client_platform_factory(
        client_id=test_client.id,
        platform="telegram",
        platform_user_id="client_tg_reminder_1",
    )

    now = datetime.now(timezone.utc)
    # 23h from now: within 24h window, so reminder_1 should fire
    starts_at = now + timedelta(hours=23)
    booking = await booking_factory(
        master_id=master.id,
        service_id=svc.id,
        client_id=test_client.id,
        starts_at=starts_at,
        status="confirmed",
    )

    # Set RLS context for the test session
    from sqlalchemy import text
    await db_session.execute(
        text(f"SET LOCAL app.current_master_id = '{master.id}'")
    )

    return {
        "master": master,
        "service": svc,
        "client": test_client,
        "platform": platform,
        "booking": booking,
        "db_session": db_session,
    }


@pytest.mark.asyncio
async def test_reminder_1_fires_within_window(reminder_setup):
    """Confirmed booking 23h from now triggers reminder_1 send when reminder_1_hours=24."""
    setup = reminder_setup
    db_session = setup["db_session"]

    with patch("app.services.reminder_service.notification_service") as mock_ns, \
         patch("app.services.reminder_service.async_session_factory") as mock_factory:
        mock_ns.send_reminder = AsyncMock(return_value=True)
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=db_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        from app.services.reminder_service import process_pending_reminders
        await process_pending_reminders()

        mock_ns.send_reminder.assert_called_once()
        call_kwargs = mock_ns.send_reminder.call_args[1] if mock_ns.send_reminder.call_args[1] else {}
        # Check it was called with keyword args or positional
        call_args = mock_ns.send_reminder.call_args
        # Verify reminder_type is "reminder_1"
        if call_args[1]:
            assert call_args[1].get("reminder_type") == "reminder_1"
        else:
            # positional: platform, platform_user_id, service_name, booking_date, booking_time, master_name, address_note, booking_id, reminder_type
            assert call_args[0][-1] == "reminder_1"


@pytest.mark.asyncio
async def test_reminder_2_fires_within_window(db_session, master_factory, service_factory, client_factory, client_platform_factory, booking_factory):
    """Confirmed booking 1.5h from now triggers reminder_2 send when reminder_2_hours=2."""
    master = await master_factory(name="R2 Master")
    master.tg_user_id = "master_r2"
    master.reminders_enabled = True
    master.reminder_1_hours = 24
    master.reminder_2_hours = 2
    master.timezone = "Europe/Moscow"
    await db_session.flush()

    svc = await service_factory(master.id, name="Nails", duration_minutes=60)
    test_client = await client_factory(name="R2 Client")
    await client_platform_factory(
        client_id=test_client.id,
        platform="telegram",
        platform_user_id="client_tg_r2",
    )

    now = datetime.now(timezone.utc)
    # 1.5h from now: within 2h window (and within 24h window too, but reminder_1 would already have been sent)
    starts_at = now + timedelta(hours=1, minutes=30)
    booking = await booking_factory(
        master_id=master.id,
        service_id=svc.id,
        client_id=test_client.id,
        starts_at=starts_at,
        status="confirmed",
    )

    # Insert a "sent" reminder_1 to simulate it was already sent
    r1 = ScheduledReminder(
        booking_id=booking.id,
        master_id=master.id,
        reminder_type="reminder_1",
        scheduled_for=starts_at - timedelta(hours=24),
        sent_at=now - timedelta(hours=10),
        status="sent",
    )
    db_session.add(r1)
    await db_session.flush()

    from sqlalchemy import text
    await db_session.execute(
        text(f"SET LOCAL app.current_master_id = '{master.id}'")
    )

    with patch("app.services.reminder_service.notification_service") as mock_ns, \
         patch("app.services.reminder_service.async_session_factory") as mock_factory:
        mock_ns.send_reminder = AsyncMock(return_value=True)
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=db_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        from app.services.reminder_service import process_pending_reminders
        await process_pending_reminders()

        # Should send reminder_2 only (reminder_1 already sent)
        mock_ns.send_reminder.assert_called_once()
        call_args = mock_ns.send_reminder.call_args
        if call_args[1]:
            assert call_args[1].get("reminder_type") == "reminder_2"
        else:
            assert call_args[0][-1] == "reminder_2"


@pytest.mark.asyncio
async def test_idempotency_no_duplicate_send(reminder_setup):
    """Already-sent reminder (ScheduledReminder status='sent') is not resent."""
    setup = reminder_setup
    db_session = setup["db_session"]
    booking = setup["booking"]
    master = setup["master"]

    # Insert a "sent" ScheduledReminder for reminder_1
    existing = ScheduledReminder(
        booking_id=booking.id,
        master_id=master.id,
        reminder_type="reminder_1",
        scheduled_for=booking.starts_at - timedelta(hours=24),
        sent_at=datetime.now(timezone.utc) - timedelta(hours=1),
        status="sent",
    )
    db_session.add(existing)
    await db_session.flush()

    with patch("app.services.reminder_service.notification_service") as mock_ns, \
         patch("app.services.reminder_service.async_session_factory") as mock_factory:
        mock_ns.send_reminder = AsyncMock(return_value=True)
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=db_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        from app.services.reminder_service import process_pending_reminders
        await process_pending_reminders()

        # reminder_1 already sent, reminder_2 not in window (23h away)
        mock_ns.send_reminder.assert_not_called()


@pytest.mark.asyncio
async def test_cancelled_booking_skipped(db_session, master_factory, service_factory, client_factory, client_platform_factory, booking_factory):
    """Cancelled booking does not trigger any reminder."""
    master = await master_factory(name="Cancel Master")
    master.tg_user_id = "master_cancel"
    master.reminders_enabled = True
    master.reminder_1_hours = 24
    master.reminder_2_hours = 2
    master.timezone = "Europe/Moscow"
    await db_session.flush()

    svc = await service_factory(master.id)
    test_client = await client_factory(name="Cancel Client")
    await client_platform_factory(
        client_id=test_client.id,
        platform="telegram",
        platform_user_id="client_tg_cancel",
    )

    now = datetime.now(timezone.utc)
    starts_at = now + timedelta(hours=23)
    booking = await booking_factory(
        master_id=master.id,
        service_id=svc.id,
        client_id=test_client.id,
        starts_at=starts_at,
        status="cancelled_by_client",
    )

    from sqlalchemy import text
    await db_session.execute(
        text(f"SET LOCAL app.current_master_id = '{master.id}'")
    )

    with patch("app.services.reminder_service.notification_service") as mock_ns, \
         patch("app.services.reminder_service.async_session_factory") as mock_factory:
        mock_ns.send_reminder = AsyncMock(return_value=True)
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=db_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        from app.services.reminder_service import process_pending_reminders
        await process_pending_reminders()

        mock_ns.send_reminder.assert_not_called()


@pytest.mark.asyncio
async def test_past_due_booking_skipped(db_session, master_factory, service_factory, client_factory, client_platform_factory, booking_factory):
    """Past-due booking (starts_at in the past) does not trigger reminder."""
    master = await master_factory(name="Past Master")
    master.tg_user_id = "master_past"
    master.reminders_enabled = True
    master.reminder_1_hours = 24
    master.reminder_2_hours = 2
    master.timezone = "Europe/Moscow"
    await db_session.flush()

    svc = await service_factory(master.id)
    test_client = await client_factory(name="Past Client")
    await client_platform_factory(
        client_id=test_client.id,
        platform="telegram",
        platform_user_id="client_tg_past",
    )

    now = datetime.now(timezone.utc)
    starts_at = now - timedelta(hours=1)  # Past
    booking = await booking_factory(
        master_id=master.id,
        service_id=svc.id,
        client_id=test_client.id,
        starts_at=starts_at,
        status="confirmed",
    )

    from sqlalchemy import text
    await db_session.execute(
        text(f"SET LOCAL app.current_master_id = '{master.id}'")
    )

    with patch("app.services.reminder_service.notification_service") as mock_ns, \
         patch("app.services.reminder_service.async_session_factory") as mock_factory:
        mock_ns.send_reminder = AsyncMock(return_value=True)
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=db_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        from app.services.reminder_service import process_pending_reminders
        await process_pending_reminders()

        mock_ns.send_reminder.assert_not_called()


@pytest.mark.asyncio
async def test_reminders_disabled_skips_all(db_session, master_factory, service_factory, client_factory, client_platform_factory, booking_factory):
    """Master with reminders_enabled=False skips all reminders."""
    master = await master_factory(name="Disabled Master")
    master.tg_user_id = "master_disabled"
    master.reminders_enabled = False  # Disabled
    master.reminder_1_hours = 24
    master.reminder_2_hours = 2
    master.timezone = "Europe/Moscow"
    await db_session.flush()

    svc = await service_factory(master.id)
    test_client = await client_factory(name="Disabled Client")
    await client_platform_factory(
        client_id=test_client.id,
        platform="telegram",
        platform_user_id="client_tg_disabled",
    )

    now = datetime.now(timezone.utc)
    starts_at = now + timedelta(hours=23)
    booking = await booking_factory(
        master_id=master.id,
        service_id=svc.id,
        client_id=test_client.id,
        starts_at=starts_at,
        status="confirmed",
    )

    from sqlalchemy import text
    await db_session.execute(
        text(f"SET LOCAL app.current_master_id = '{master.id}'")
    )

    with patch("app.services.reminder_service.notification_service") as mock_ns, \
         patch("app.services.reminder_service.async_session_factory") as mock_factory:
        mock_ns.send_reminder = AsyncMock(return_value=True)
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=db_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        from app.services.reminder_service import process_pending_reminders
        await process_pending_reminders()

        mock_ns.send_reminder.assert_not_called()


@pytest.mark.asyncio
async def test_reminder_2_none_skips_second(reminder_setup):
    """Master with reminder_2_hours=None skips second reminder."""
    setup = reminder_setup
    db_session = setup["db_session"]
    master = setup["master"]
    booking = setup["booking"]

    # Set reminder_2_hours to None
    master.reminder_2_hours = None
    # Also move booking to be 1.5h away so reminder_2 window would match if enabled
    now = datetime.now(timezone.utc)
    booking.starts_at = now + timedelta(hours=1, minutes=30)
    booking.ends_at = booking.starts_at + timedelta(hours=1)
    await db_session.flush()

    # Insert sent reminder_1 so we only test reminder_2
    r1 = ScheduledReminder(
        booking_id=booking.id,
        master_id=master.id,
        reminder_type="reminder_1",
        scheduled_for=booking.starts_at - timedelta(hours=24),
        sent_at=now - timedelta(hours=10),
        status="sent",
    )
    db_session.add(r1)
    await db_session.flush()

    with patch("app.services.reminder_service.notification_service") as mock_ns, \
         patch("app.services.reminder_service.async_session_factory") as mock_factory:
        mock_ns.send_reminder = AsyncMock(return_value=True)
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=db_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        from app.services.reminder_service import process_pending_reminders
        await process_pending_reminders()

        # Should NOT send reminder_2 since it's disabled
        mock_ns.send_reminder.assert_not_called()


@pytest.mark.asyncio
async def test_cleanup_reminders_for_booking(reminder_setup):
    """cleanup_reminders_for_booking deletes pending rows."""
    setup = reminder_setup
    db_session = setup["db_session"]
    booking = setup["booking"]
    master = setup["master"]

    # Insert a pending reminder
    pending = ScheduledReminder(
        booking_id=booking.id,
        master_id=master.id,
        reminder_type="reminder_1",
        scheduled_for=booking.starts_at - timedelta(hours=24),
        status="pending",
    )
    db_session.add(pending)
    await db_session.flush()

    from app.services.reminder_service import cleanup_reminders_for_booking
    await cleanup_reminders_for_booking(db_session, booking.id)

    # Verify pending row deleted
    from sqlalchemy import select
    result = await db_session.execute(
        select(ScheduledReminder).where(
            ScheduledReminder.booking_id == booking.id,
            ScheduledReminder.status == "pending",
        )
    )
    rows = result.scalars().all()
    assert len(rows) == 0
