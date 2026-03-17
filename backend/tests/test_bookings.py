"""Tests for Booking CRUD endpoints."""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest


def _next_weekday(day_of_week: int):
    """Return the next date that falls on the given weekday (0=Mon)."""
    from datetime import date

    today = date.today()
    days_ahead = day_of_week - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)


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


@pytest.mark.asyncio
async def test_create_booking_success(client, auth_headers, service_factory):
    headers, master = auth_headers

    # Setup schedule
    await client.put(
        "/api/v1/schedule", json=_make_schedule_template(), headers=headers
    )

    svc = await service_factory(master.id, duration_minutes=60)

    target = _next_weekday(0)  # Monday
    tz = ZoneInfo("Europe/Moscow")
    starts_at = datetime.combine(target, time(10, 0), tzinfo=tz)

    resp = await client.post(
        "/api/v1/bookings",
        json={
            "master_id": str(master.id),
            "service_id": str(svc.id),
            "starts_at": starts_at.isoformat(),
            "client_name": "Ivan Petrov",
            "client_phone": "+79161234567",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "confirmed"
    assert data["service_name"] == svc.name
    assert data["client_name"] == "Ivan Petrov"


@pytest.mark.asyncio
async def test_create_booking_auto_creates_client(
    client, auth_headers, service_factory, db_session
):
    headers, master = auth_headers
    await client.put(
        "/api/v1/schedule", json=_make_schedule_template(), headers=headers
    )
    svc = await service_factory(master.id, duration_minutes=30)

    target = _next_weekday(1)  # Tuesday
    tz = ZoneInfo("Europe/Moscow")
    starts_at = datetime.combine(target, time(11, 0), tzinfo=tz)

    resp = await client.post(
        "/api/v1/bookings",
        json={
            "master_id": str(master.id),
            "service_id": str(svc.id),
            "starts_at": starts_at.isoformat(),
            "client_name": "Anna Smirnova",
            "client_phone": "+79167654321",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["client_phone"] == "+79167654321"


@pytest.mark.asyncio
async def test_create_booking_reuses_existing_client(
    client, auth_headers, service_factory
):
    headers, master = auth_headers
    await client.put(
        "/api/v1/schedule", json=_make_schedule_template(), headers=headers
    )
    svc = await service_factory(master.id, duration_minutes=30)

    tz = ZoneInfo("Europe/Moscow")
    phone = "+79160001111"

    # First booking
    target1 = _next_weekday(0)
    starts_at1 = datetime.combine(target1, time(9, 0), tzinfo=tz)
    resp1 = await client.post(
        "/api/v1/bookings",
        json={
            "master_id": str(master.id),
            "service_id": str(svc.id),
            "starts_at": starts_at1.isoformat(),
            "client_name": "Reuse Client",
            "client_phone": phone,
        },
    )
    assert resp1.status_code == 201
    client_id_1 = resp1.json()["client_id"]

    # Second booking with same phone (different time)
    starts_at2 = datetime.combine(target1, time(15, 0), tzinfo=tz)
    resp2 = await client.post(
        "/api/v1/bookings",
        json={
            "master_id": str(master.id),
            "service_id": str(svc.id),
            "starts_at": starts_at2.isoformat(),
            "client_name": "Reuse Client",
            "client_phone": phone,
        },
    )
    assert resp2.status_code == 201
    client_id_2 = resp2.json()["client_id"]

    # Same client reused
    assert client_id_1 == client_id_2


@pytest.mark.asyncio
async def test_double_booking_rejected(client, auth_headers, service_factory):
    headers, master = auth_headers
    await client.put(
        "/api/v1/schedule", json=_make_schedule_template(), headers=headers
    )
    svc = await service_factory(master.id, duration_minutes=60)

    target = _next_weekday(2)  # Wednesday
    tz = ZoneInfo("Europe/Moscow")
    starts_at = datetime.combine(target, time(14, 0), tzinfo=tz)

    # First booking succeeds
    resp1 = await client.post(
        "/api/v1/bookings",
        json={
            "master_id": str(master.id),
            "service_id": str(svc.id),
            "starts_at": starts_at.isoformat(),
            "client_name": "Client A",
            "client_phone": "+79161111111",
        },
    )
    assert resp1.status_code == 201

    # Second booking for same slot gets 409
    resp2 = await client.post(
        "/api/v1/bookings",
        json={
            "master_id": str(master.id),
            "service_id": str(svc.id),
            "starts_at": starts_at.isoformat(),
            "client_name": "Client B",
            "client_phone": "+79162222222",
        },
    )
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_cancel_booking_by_master(client, auth_headers, service_factory):
    headers, master = auth_headers
    await client.put(
        "/api/v1/schedule", json=_make_schedule_template(), headers=headers
    )
    svc = await service_factory(master.id, duration_minutes=60)

    target = _next_weekday(3)  # Thursday
    tz = ZoneInfo("Europe/Moscow")
    starts_at = datetime.combine(target, time(10, 0), tzinfo=tz)

    create_resp = await client.post(
        "/api/v1/bookings",
        json={
            "master_id": str(master.id),
            "service_id": str(svc.id),
            "starts_at": starts_at.isoformat(),
            "client_name": "Cancel Test",
            "client_phone": "+79163333333",
        },
    )
    booking_id = create_resp.json()["id"]

    # Master cancels (with auth headers)
    cancel_resp = await client.put(
        f"/api/v1/bookings/{booking_id}/cancel",
        json={},
        headers=headers,
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled_by_master"


@pytest.mark.asyncio
async def test_cancel_booking_by_client_within_deadline(
    client, auth_headers, service_factory, db_session
):
    headers, master = auth_headers
    # Set cancellation deadline to 48 hours
    master.cancellation_deadline_hours = 48
    await db_session.flush()

    await client.put(
        "/api/v1/schedule", json=_make_schedule_template(), headers=headers
    )
    svc = await service_factory(master.id, duration_minutes=60)

    # Booking 1 hour from now (within 48h deadline)
    tz = ZoneInfo("Europe/Moscow")
    starts_at = datetime.now(tz) + timedelta(hours=1)

    create_resp = await client.post(
        "/api/v1/bookings",
        json={
            "master_id": str(master.id),
            "service_id": str(svc.id),
            "starts_at": starts_at.isoformat(),
            "client_name": "Deadline Test",
            "client_phone": "+79164444444",
        },
    )
    booking_id = create_resp.json()["id"]

    # Client cancels (no auth headers -- treated as client)
    cancel_resp = await client.put(
        f"/api/v1/bookings/{booking_id}/cancel",
        json={},
    )
    # Should fail: within deadline
    assert cancel_resp.status_code == 400
    assert "deadline" in cancel_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cancel_booking_by_client_before_deadline(
    client, auth_headers, service_factory, db_session
):
    headers, master = auth_headers
    master.cancellation_deadline_hours = 2
    await db_session.flush()

    await client.put(
        "/api/v1/schedule", json=_make_schedule_template(), headers=headers
    )
    svc = await service_factory(master.id, duration_minutes=60)

    # Booking far in the future (well before 2h deadline)
    target = _next_weekday(4)  # Friday
    tz = ZoneInfo("Europe/Moscow")
    starts_at = datetime.combine(target, time(16, 0), tzinfo=tz)

    create_resp = await client.post(
        "/api/v1/bookings",
        json={
            "master_id": str(master.id),
            "service_id": str(svc.id),
            "starts_at": starts_at.isoformat(),
            "client_name": "Before Deadline",
            "client_phone": "+79165555555",
        },
    )
    booking_id = create_resp.json()["id"]

    # Client cancels (no auth -- before deadline)
    cancel_resp = await client.put(
        f"/api/v1/bookings/{booking_id}/cancel",
        json={},
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled_by_client"


@pytest.mark.asyncio
async def test_reschedule_booking(client, auth_headers, service_factory):
    headers, master = auth_headers
    await client.put(
        "/api/v1/schedule", json=_make_schedule_template(), headers=headers
    )
    svc = await service_factory(master.id, duration_minutes=60)

    target = _next_weekday(0)
    tz = ZoneInfo("Europe/Moscow")
    starts_at = datetime.combine(target, time(10, 0), tzinfo=tz)

    create_resp = await client.post(
        "/api/v1/bookings",
        json={
            "master_id": str(master.id),
            "service_id": str(svc.id),
            "starts_at": starts_at.isoformat(),
            "client_name": "Reschedule Test",
            "client_phone": "+79166666666",
        },
    )
    booking_id = create_resp.json()["id"]

    new_time = datetime.combine(target, time(14, 0), tzinfo=tz)
    reschedule_resp = await client.put(
        f"/api/v1/bookings/{booking_id}/reschedule",
        json={"new_starts_at": new_time.isoformat()},
        headers=headers,
    )
    assert reschedule_resp.status_code == 200
    data = reschedule_resp.json()
    # Verify time changed
    assert "14:00" in data["starts_at"]


@pytest.mark.asyncio
async def test_list_bookings_with_date_filter(
    client, auth_headers, service_factory
):
    headers, master = auth_headers
    await client.put(
        "/api/v1/schedule", json=_make_schedule_template(), headers=headers
    )
    svc = await service_factory(master.id, duration_minutes=30)

    tz = ZoneInfo("Europe/Moscow")
    target = _next_weekday(1)
    starts_at = datetime.combine(target, time(9, 0), tzinfo=tz)

    await client.post(
        "/api/v1/bookings",
        json={
            "master_id": str(master.id),
            "service_id": str(svc.id),
            "starts_at": starts_at.isoformat(),
            "client_name": "Filter Test",
            "client_phone": "+79167777777",
        },
    )

    # Filter by date range that includes the booking
    resp = await client.get(
        "/api/v1/bookings",
        params={
            "date_from": target.isoformat(),
            "date_to": (target + timedelta(days=1)).isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_manual_booking(client, auth_headers, service_factory):
    headers, master = auth_headers
    await client.put(
        "/api/v1/schedule", json=_make_schedule_template(), headers=headers
    )
    svc = await service_factory(master.id, duration_minutes=60)

    target = _next_weekday(3)
    tz = ZoneInfo("Europe/Moscow")
    starts_at = datetime.combine(target, time(11, 0), tzinfo=tz)

    resp = await client.post(
        "/api/v1/bookings/manual",
        json={
            "service_id": str(svc.id),
            "starts_at": starts_at.isoformat(),
            "client_name": "Manual Client",
            "client_phone": "+79168888888",
            "notes": "Walk-in",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["source_platform"] == "web"
    assert data["client_name"] == "Manual Client"
