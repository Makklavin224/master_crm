"""Tests for Client list and history endpoints."""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest


def _next_weekday(day_of_week: int):
    from datetime import date

    today = date.today()
    days_ahead = day_of_week - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)


def _make_schedule_template():
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
async def test_list_clients_empty(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.get("/api/v1/clients", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_clients_after_booking(
    client, auth_headers, service_factory
):
    headers, master = auth_headers
    await client.put(
        "/api/v1/schedule", json=_make_schedule_template(), headers=headers
    )
    svc = await service_factory(master.id, duration_minutes=30)

    target = _next_weekday(0)
    tz = ZoneInfo("Europe/Moscow")
    starts_at = datetime.combine(target, time(9, 0), tzinfo=tz)

    await client.post(
        "/api/v1/bookings",
        json={
            "master_id": str(master.id),
            "service_id": str(svc.id),
            "starts_at": starts_at.isoformat(),
            "client_name": "Visited Client",
            "client_phone": "+79161112233",
        },
    )

    resp = await client.get("/api/v1/clients", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1

    found = next(
        (c for c in data if c["client"]["phone"] == "+79161112233"), None
    )
    assert found is not None
    assert found["visit_count"] == 1


@pytest.mark.asyncio
async def test_client_detail_with_history(
    client, auth_headers, service_factory
):
    headers, master = auth_headers
    await client.put(
        "/api/v1/schedule", json=_make_schedule_template(), headers=headers
    )
    svc = await service_factory(master.id, duration_minutes=30)

    target = _next_weekday(1)
    tz = ZoneInfo("Europe/Moscow")
    starts_at = datetime.combine(target, time(10, 0), tzinfo=tz)

    booking_resp = await client.post(
        "/api/v1/bookings",
        json={
            "master_id": str(master.id),
            "service_id": str(svc.id),
            "starts_at": starts_at.isoformat(),
            "client_name": "Detail Client",
            "client_phone": "+79163344556",
        },
    )
    client_id = booking_resp.json()["client_id"]

    resp = await client.get(f"/api/v1/clients/{client_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["client"]["name"] == "Detail Client"
    assert data["visit_count"] >= 1
    assert len(data["bookings"]) >= 1


@pytest.mark.asyncio
async def test_clients_rls_isolation(
    client, auth_headers, master_factory, service_factory, db_session, app_with_db
):
    """Master A cannot see Master B's clients."""
    headers_a, master_a = auth_headers

    # Create second master
    from app.core.security import create_access_token

    master_b = await master_factory(name="Master B")
    token_b = create_access_token(data={"sub": str(master_b.id)})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Create schedule for master A
    await client.put(
        "/api/v1/schedule", json=_make_schedule_template(), headers=headers_a
    )

    # Create service for master A
    svc_a = await service_factory(master_a.id, name="Service A")

    target = _next_weekday(2)
    tz = ZoneInfo("Europe/Moscow")
    starts_at = datetime.combine(target, time(9, 0), tzinfo=tz)

    # Book a client under master A
    await client.post(
        "/api/v1/bookings",
        json={
            "master_id": str(master_a.id),
            "service_id": str(svc_a.id),
            "starts_at": starts_at.isoformat(),
            "client_name": "A-Only Client",
            "client_phone": "+79169998877",
        },
    )

    # Master A can see the client
    resp_a = await client.get("/api/v1/clients", headers=headers_a)
    assert resp_a.status_code == 200
    phones_a = [c["client"]["phone"] for c in resp_a.json()]
    assert "+79169998877" in phones_a

    # Master B should NOT see Master A's client
    resp_b = await client.get("/api/v1/clients", headers=headers_b)
    assert resp_b.status_code == 200
    phones_b = [c["client"]["phone"] for c in resp_b.json()]
    assert "+79169998877" not in phones_b
