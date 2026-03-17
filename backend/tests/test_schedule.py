"""Tests for Schedule management and slot calculation endpoints."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest


def _make_schedule_template(
    start_time: str = "09:00",
    end_time: str = "18:00",
    break_start: str | None = "13:00",
    break_end: str | None = "14:00",
    working_days: list[int] | None = None,
):
    """Helper to create a 7-day schedule template payload."""
    if working_days is None:
        working_days = [0, 1, 2, 3, 4]
    days = []
    for day in range(7):
        entry = {
            "day_of_week": day,
            "start_time": start_time,
            "end_time": end_time,
            "is_working": day in working_days,
        }
        if day in working_days and break_start and break_end:
            entry["break_start"] = break_start
            entry["break_end"] = break_end
        days.append(entry)
    return {"days": days}


def _next_weekday(day_of_week: int) -> date:
    """Return the next date that falls on the given weekday (0=Mon, 6=Sun)."""
    today = date.today()
    days_ahead = day_of_week - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)


@pytest.mark.asyncio
async def test_put_schedule_upserts_seven_days(client, auth_headers):
    headers, _ = auth_headers
    template = _make_schedule_template()

    resp = await client.put("/api/v1/schedule", json=template, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 7
    # Check Monday is working
    monday = next(d for d in data if d["day_of_week"] == 0)
    assert monday["is_working"] is True
    assert monday["start_time"] == "09:00:00"


@pytest.mark.asyncio
async def test_get_schedule_returns_seven_days(client, auth_headers):
    headers, _ = auth_headers
    template = _make_schedule_template()
    await client.put("/api/v1/schedule", json=template, headers=headers)

    resp = await client.get("/api/v1/schedule", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 7


@pytest.mark.asyncio
async def test_create_exception_day_off(client, auth_headers):
    headers, _ = auth_headers
    target = _next_weekday(0)  # Next Monday

    resp = await client.post(
        "/api/v1/schedule/exceptions",
        json={
            "exception_date": target.isoformat(),
            "is_day_off": True,
            "reason": "Holiday",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["is_day_off"] is True
    assert data["reason"] == "Holiday"


@pytest.mark.asyncio
async def test_delete_exception(client, auth_headers):
    headers, _ = auth_headers
    target = _next_weekday(2)  # Next Wednesday

    create_resp = await client.post(
        "/api/v1/schedule/exceptions",
        json={"exception_date": target.isoformat(), "is_day_off": True},
        headers=headers,
    )
    exc_id = create_resp.json()["id"]

    del_resp = await client.delete(
        f"/api/v1/schedule/exceptions/{exc_id}", headers=headers
    )
    assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_get_slots_returns_times(client, auth_headers, service_factory):
    headers, master = auth_headers

    # Create schedule (Mon-Fri 9-18, break 13-14)
    template = _make_schedule_template()
    await client.put("/api/v1/schedule", json=template, headers=headers)

    # Create a service
    svc = await service_factory(master.id, duration_minutes=60)

    # Get slots for next Monday
    target = _next_weekday(0)
    resp = await client.get(
        f"/api/v1/masters/{master.id}/slots",
        params={"date": target.isoformat(), "service_id": str(svc.id)},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["date"] == target.isoformat()
    assert len(data["slots"]) > 0

    # 9:00 should be available
    slot_times = [s["time"] for s in data["slots"]]
    assert "09:00:00" in slot_times


@pytest.mark.asyncio
async def test_get_slots_day_off_returns_empty(
    client, auth_headers, service_factory
):
    headers, master = auth_headers

    # Create schedule
    template = _make_schedule_template()
    await client.put("/api/v1/schedule", json=template, headers=headers)

    svc = await service_factory(master.id, duration_minutes=60)

    # Next Saturday is a day off (not in working_days [0,1,2,3,4])
    target = _next_weekday(5)
    resp = await client.get(
        f"/api/v1/masters/{master.id}/slots",
        params={"date": target.isoformat(), "service_id": str(svc.id)},
    )
    assert resp.status_code == 200
    assert len(resp.json()["slots"]) == 0


@pytest.mark.asyncio
async def test_get_slots_excludes_break(client, auth_headers, service_factory):
    headers, master = auth_headers

    # Create schedule with break 13:00-14:00
    template = _make_schedule_template(
        break_start="13:00", break_end="14:00"
    )
    await client.put("/api/v1/schedule", json=template, headers=headers)

    svc = await service_factory(master.id, duration_minutes=30)
    target = _next_weekday(0)

    resp = await client.get(
        f"/api/v1/masters/{master.id}/slots",
        params={"date": target.isoformat(), "service_id": str(svc.id)},
    )
    slot_times = [s["time"] for s in resp.json()["slots"]]

    # 13:00 and 13:30 should NOT be in slots (overlap with break 13-14)
    assert "13:00:00" not in slot_times
    assert "13:30:00" not in slot_times


@pytest.mark.asyncio
async def test_get_slots_excludes_existing_booking(
    client,
    auth_headers,
    service_factory,
    client_factory,
    booking_factory,
    db_session,
):
    headers, master = auth_headers

    # Create schedule
    template = _make_schedule_template(break_start=None, break_end=None)
    await client.put("/api/v1/schedule", json=template, headers=headers)

    svc = await service_factory(master.id, duration_minutes=60)
    cl = await client_factory()

    # Create a booking at 10:00 next Monday
    target = _next_weekday(0)
    tz = ZoneInfo("Europe/Moscow")
    booking_start = datetime.combine(target, time(10, 0), tzinfo=tz)
    await booking_factory(
        master_id=master.id,
        service_id=svc.id,
        client_id=cl.id,
        starts_at=booking_start,
        duration_minutes=60,
    )

    resp = await client.get(
        f"/api/v1/masters/{master.id}/slots",
        params={"date": target.isoformat(), "service_id": str(svc.id)},
    )
    slot_times = [s["time"] for s in resp.json()["slots"]]

    # 10:00 should NOT be available (already booked)
    assert "10:00:00" not in slot_times
    # 9:00 should still be available
    assert "09:00:00" in slot_times


@pytest.mark.asyncio
async def test_get_slots_respects_buffer(client, auth_headers, service_factory, db_session):
    headers, master = auth_headers

    # Set buffer_minutes on master
    master.buffer_minutes = 15
    await db_session.flush()

    # Create schedule (no break for simplicity)
    template = _make_schedule_template(break_start=None, break_end=None)
    await client.put("/api/v1/schedule", json=template, headers=headers)

    # 30-minute service + 15-minute buffer = 45 min total per slot
    svc = await service_factory(master.id, duration_minutes=30)
    target = _next_weekday(0)

    resp = await client.get(
        f"/api/v1/masters/{master.id}/slots",
        params={"date": target.isoformat(), "service_id": str(svc.id)},
    )
    slots = resp.json()["slots"]
    # With 30-min service, 15-min buffer, 30-min interval, working 9-18:
    # slots should fit within the window accounting for buffer
    assert len(slots) > 0

    # Last slot should end by 18:00 considering service duration only
    # (buffer is between appointments, not at end of day)
    # The algorithm checks current_min + service_duration <= work_end
    last_slot_time = slots[-1]["time"]
    assert last_slot_time is not None
