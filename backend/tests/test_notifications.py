"""Tests for notification infrastructure: booking confirmations, master alerts,
notification settings API, and client cancel callback."""

import uuid
from datetime import datetime, time, timedelta
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

import pytest

from app.models.client import ClientPlatform


# ---------------------------------------------------------------------------
# Notification settings API tests (BOOK-07)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_notification_settings_defaults(client, auth_headers):
    """GET /api/v1/settings/notifications returns default values."""
    headers, _ = auth_headers
    resp = await client.get("/api/v1/settings/notifications", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["reminders_enabled"] is True
    assert data["reminder_1_hours"] == 24
    assert data["reminder_2_hours"] == 2
    assert data["address_note"] is None


@pytest.mark.asyncio
async def test_update_notification_settings(client, auth_headers):
    """PUT /api/v1/settings/notifications updates values."""
    headers, _ = auth_headers
    resp = await client.put(
        "/api/v1/settings/notifications",
        json={"reminder_1_hours": 12, "address_note": "ул. Ленина 5"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["reminder_1_hours"] == 12
    assert data["address_note"] == "ул. Ленина 5"


@pytest.mark.asyncio
async def test_update_notification_settings_invalid_interval(client, auth_headers):
    """PUT with invalid interval returns 422."""
    headers, _ = auth_headers
    resp = await client.put(
        "/api/v1/settings/notifications",
        json={"reminder_1_hours": 3},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_disable_second_reminder(client, auth_headers):
    """PUT with reminder_2_hours=null disables second reminder."""
    headers, _ = auth_headers
    resp = await client.put(
        "/api/v1/settings/notifications",
        json={"reminder_2_hours": None},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["reminder_2_hours"] is None


# ---------------------------------------------------------------------------
# Booking confirmation tests (NOTF-03)
# ---------------------------------------------------------------------------


def _make_schedule_template():
    """Mon-Fri 9-18, no break."""
    days = []
    for day in range(7):
        days.append(
            {
                "day_of_week": day,
                "start_time": "09:00",
                "end_time": "18:00",
                "is_working": day < 5,
            }
        )
    return {"days": days}


def _next_weekday(day_of_week: int):
    """Return the next date that falls on the given weekday (0=Mon)."""
    from datetime import date

    today = date.today()
    days_ahead = day_of_week - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)


@pytest.mark.asyncio
async def test_booking_confirmation_sent(
    client, auth_headers, service_factory, db_session
):
    """After creating a booking, send_booking_confirmation is called."""
    headers, master = auth_headers

    # Create a client with telegram platform
    from app.models.client import Client

    test_client = Client(phone="+79161110001", name="Confirm Client")
    db_session.add(test_client)
    await db_session.flush()

    platform = ClientPlatform(
        client_id=test_client.id,
        platform="telegram",
        platform_user_id="123456789",
    )
    db_session.add(platform)
    await db_session.flush()

    # Setup schedule
    await client.put(
        "/api/v1/schedule", json=_make_schedule_template(), headers=headers
    )
    svc = await service_factory(master.id, duration_minutes=60)

    target = _next_weekday(0)
    tz = ZoneInfo("Europe/Moscow")
    starts_at = datetime.combine(target, time(10, 0), tzinfo=tz)

    with patch(
        "app.services.booking_service.notification_service"
    ) as mock_ns:
        mock_ns.send_booking_notification = AsyncMock(return_value=True)
        mock_ns.send_booking_confirmation = AsyncMock(return_value=True)

        resp = await client.post(
            "/api/v1/bookings",
            json={
                "master_id": str(master.id),
                "service_id": str(svc.id),
                "starts_at": starts_at.isoformat(),
                "client_name": "Confirm Client",
                "client_phone": "+79161110001",
                "tg_user_id": "123456789",
            },
        )
        assert resp.status_code == 201

        # Verify send_booking_confirmation was called
        mock_ns.send_booking_confirmation.assert_called_once()
        call_kwargs = mock_ns.send_booking_confirmation.call_args
        # First positional arg is platform
        assert call_kwargs[1]["platform"] == "telegram" or call_kwargs[0][0] == "telegram"


@pytest.mark.asyncio
async def test_booking_confirmation_no_platform(
    client, auth_headers, service_factory, db_session
):
    """Booking for client without ClientPlatform skips confirmation gracefully."""
    headers, master = auth_headers

    await client.put(
        "/api/v1/schedule", json=_make_schedule_template(), headers=headers
    )
    svc = await service_factory(master.id, duration_minutes=60)

    target = _next_weekday(1)
    tz = ZoneInfo("Europe/Moscow")
    starts_at = datetime.combine(target, time(10, 0), tzinfo=tz)

    with patch(
        "app.services.booking_service.notification_service"
    ) as mock_ns:
        mock_ns.send_booking_notification = AsyncMock(return_value=True)
        mock_ns.send_booking_confirmation = AsyncMock(return_value=True)

        resp = await client.post(
            "/api/v1/bookings",
            json={
                "master_id": str(master.id),
                "service_id": str(svc.id),
                "starts_at": starts_at.isoformat(),
                "client_name": "No Platform Client",
                "client_phone": "+79161110002",
            },
        )
        assert resp.status_code == 201

        # send_booking_confirmation should NOT be called (no platform record)
        mock_ns.send_booking_confirmation.assert_not_called()


# ---------------------------------------------------------------------------
# Master alert tests (BOOK-07)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_master_notified_on_new_booking(
    client, auth_headers, service_factory, db_session
):
    """Master receives notification when new booking is created."""
    headers, master = auth_headers
    master.tg_user_id = "master_tg_111"
    await db_session.flush()

    await client.put(
        "/api/v1/schedule", json=_make_schedule_template(), headers=headers
    )
    svc = await service_factory(master.id, duration_minutes=60)

    target = _next_weekday(2)
    tz = ZoneInfo("Europe/Moscow")
    starts_at = datetime.combine(target, time(10, 0), tzinfo=tz)

    with patch(
        "app.services.booking_service.notification_service"
    ) as mock_ns:
        mock_ns.send_booking_notification = AsyncMock(return_value=True)
        mock_ns.send_booking_confirmation = AsyncMock(return_value=True)

        resp = await client.post(
            "/api/v1/bookings",
            json={
                "master_id": str(master.id),
                "service_id": str(svc.id),
                "starts_at": starts_at.isoformat(),
                "client_name": "Alert Client",
                "client_phone": "+79161110003",
            },
        )
        assert resp.status_code == 201
        mock_ns.send_booking_notification.assert_called_once()
        call_args = mock_ns.send_booking_notification.call_args
        notif = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("notif")
        assert notif.notification_type == "new"


@pytest.mark.asyncio
async def test_master_notified_on_cancellation(
    client, auth_headers, service_factory, db_session
):
    """Master receives notification when booking is cancelled."""
    headers, master = auth_headers
    master.tg_user_id = "master_tg_222"
    await db_session.flush()

    await client.put(
        "/api/v1/schedule", json=_make_schedule_template(), headers=headers
    )
    svc = await service_factory(master.id, duration_minutes=60)

    target = _next_weekday(3)
    tz = ZoneInfo("Europe/Moscow")
    starts_at = datetime.combine(target, time(10, 0), tzinfo=tz)

    with patch(
        "app.services.booking_service.notification_service"
    ) as mock_ns:
        mock_ns.send_booking_notification = AsyncMock(return_value=True)
        mock_ns.send_booking_confirmation = AsyncMock(return_value=True)
        mock_ns.send_message = AsyncMock(return_value=True)

        # Create booking
        resp = await client.post(
            "/api/v1/bookings",
            json={
                "master_id": str(master.id),
                "service_id": str(svc.id),
                "starts_at": starts_at.isoformat(),
                "client_name": "Cancel Alert Client",
                "client_phone": "+79161110004",
            },
        )
        assert resp.status_code == 201
        booking_id = resp.json()["id"]

        mock_ns.send_booking_notification.reset_mock()

        # Cancel booking
        cancel_resp = await client.put(
            f"/api/v1/bookings/{booking_id}/cancel",
            json={},
            headers=headers,
        )
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "cancelled_by_master"

        mock_ns.send_booking_notification.assert_called_once()
        call_args = mock_ns.send_booking_notification.call_args
        notif = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("notif")
        assert notif.notification_type == "cancelled"


@pytest.mark.asyncio
async def test_master_notified_on_reschedule(
    client, auth_headers, service_factory, db_session
):
    """Master receives notification when booking is rescheduled."""
    headers, master = auth_headers
    master.tg_user_id = "master_tg_333"
    await db_session.flush()

    await client.put(
        "/api/v1/schedule", json=_make_schedule_template(), headers=headers
    )
    svc = await service_factory(master.id, duration_minutes=60)

    target = _next_weekday(4)
    tz = ZoneInfo("Europe/Moscow")
    starts_at = datetime.combine(target, time(10, 0), tzinfo=tz)

    with patch(
        "app.services.booking_service.notification_service"
    ) as mock_ns:
        mock_ns.send_booking_notification = AsyncMock(return_value=True)
        mock_ns.send_booking_confirmation = AsyncMock(return_value=True)
        mock_ns.send_message = AsyncMock(return_value=True)

        resp = await client.post(
            "/api/v1/bookings",
            json={
                "master_id": str(master.id),
                "service_id": str(svc.id),
                "starts_at": starts_at.isoformat(),
                "client_name": "Reschedule Alert Client",
                "client_phone": "+79161110005",
            },
        )
        assert resp.status_code == 201
        booking_id = resp.json()["id"]

        mock_ns.send_booking_notification.reset_mock()

        new_time = datetime.combine(target, time(15, 0), tzinfo=tz)
        reschedule_resp = await client.put(
            f"/api/v1/bookings/{booking_id}/reschedule",
            json={"new_starts_at": new_time.isoformat()},
            headers=headers,
        )
        assert reschedule_resp.status_code == 200

        mock_ns.send_booking_notification.assert_called_once()
        call_args = mock_ns.send_booking_notification.call_args
        notif = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("notif")
        assert notif.notification_type == "rescheduled"


# ---------------------------------------------------------------------------
# Client cancel callback tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancel_client_callback_success(
    db_session,
    master_factory,
    service_factory,
    client_factory,
    booking_factory,
):
    """cancel_client:{id} callback cancels booking successfully."""
    master = await master_factory(name="CB Master")
    master.tg_user_id = "master_cb_111"
    master.cancellation_deadline_hours = 2
    await db_session.flush()

    svc = await service_factory(master.id)
    test_client = await client_factory(name="CB Client")

    # Add telegram platform for the client
    platform = ClientPlatform(
        client_id=test_client.id,
        platform="telegram",
        platform_user_id="client_tg_111",
    )
    db_session.add(platform)
    await db_session.flush()

    # Booking far in the future (beyond deadline)
    tz = ZoneInfo("Europe/Moscow")
    starts_at = datetime.now(tz) + timedelta(days=3)
    booking = await booking_factory(
        master_id=master.id,
        service_id=svc.id,
        client_id=test_client.id,
        starts_at=starts_at,
    )

    # Simulate the cancel_client callback
    from app.services.booking_service import cancel_booking

    result = await cancel_booking(
        db=db_session,
        booking_id=booking.id,
        cancelled_by="client",
        cancellation_deadline_hours=master.cancellation_deadline_hours,
    )
    assert result.status == "cancelled_by_client"


@pytest.mark.asyncio
async def test_cancel_client_callback_deadline_passed(
    db_session,
    master_factory,
    service_factory,
    client_factory,
    booking_factory,
):
    """cancel_client:{id} callback fails when deadline has passed."""
    master = await master_factory(name="CB Master 2")
    master.tg_user_id = "master_cb_222"
    master.cancellation_deadline_hours = 24
    await db_session.flush()

    svc = await service_factory(master.id)
    test_client = await client_factory(name="CB Client 2")

    # Booking in 1 hour (within 24h deadline)
    tz = ZoneInfo("Europe/Moscow")
    starts_at = datetime.now(tz) + timedelta(hours=1)
    booking = await booking_factory(
        master_id=master.id,
        service_id=svc.id,
        client_id=test_client.id,
        starts_at=starts_at,
    )

    from fastapi import HTTPException
    from app.services.booking_service import cancel_booking

    with pytest.raises(HTTPException) as exc_info:
        await cancel_booking(
            db=db_session,
            booking_id=booking.id,
            cancelled_by="client",
            cancellation_deadline_hours=master.cancellation_deadline_hours,
        )
    assert exc_info.value.status_code == 400
    assert "deadline" in exc_info.value.detail.lower()
