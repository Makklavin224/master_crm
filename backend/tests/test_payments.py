"""Integration tests for payment API endpoints.

Requires running PostgreSQL test database (via Docker).
Tests cover: manual payment, Robokassa payment + callback, payment history,
cancel, and requisites flows.
"""

import uuid
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import text

from app.core.security import create_access_token


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


@pytest.fixture
async def payment_setup(
    client,
    auth_headers,
    service_factory,
    client_factory,
    booking_factory,
    db_session,
):
    """Set up a master, service, client, and confirmed booking for payment tests."""
    headers, master = auth_headers

    # Set RLS context for the master
    await db_session.execute(
        text("SET LOCAL app.current_master_id = :mid"),
        {"mid": str(master.id)},
    )

    # Create sequence if not exists (Alembic migration creates it, but tests use metadata)
    try:
        await db_session.execute(
            text("CREATE SEQUENCE IF NOT EXISTS robokassa_inv_id_seq")
        )
    except Exception:
        pass  # May already exist

    svc = await service_factory(master.id, name="Manicure", price=150000)
    test_client = await client_factory(name="Test Client", phone="+79161234567")
    booking = await booking_factory(
        master_id=master.id,
        service_id=svc.id,
        client_id=test_client.id,
        status="confirmed",
    )

    return {
        "headers": headers,
        "master": master,
        "service": svc,
        "client": test_client,
        "booking": booking,
        "db_session": db_session,
    }


# --- Manual payment ---


@pytest.mark.asyncio
async def test_create_manual_payment(client, payment_setup):
    setup = payment_setup
    resp = await client.post(
        "/api/v1/payments/manual",
        json={
            "booking_id": str(setup["booking"].id),
            "payment_method": "cash",
        },
        headers=setup["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "paid"
    assert data["payment_method"] == "cash"
    assert data["amount"] == 150000


@pytest.mark.asyncio
async def test_create_manual_payment_invalid_booking(client, payment_setup):
    setup = payment_setup
    fake_id = str(uuid.uuid4())
    resp = await client.post(
        "/api/v1/payments/manual",
        json={
            "booking_id": fake_id,
            "payment_method": "cash",
        },
        headers=setup["headers"],
    )
    assert resp.status_code == 404


# --- Payment history ---


@pytest.mark.asyncio
async def test_payment_history_empty(client, auth_headers, db_session):
    headers, master = auth_headers
    await db_session.execute(
        text("SET LOCAL app.current_master_id = :mid"),
        {"mid": str(master.id)},
    )
    resp = await client.get(
        "/api/v1/payments/history",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_payment_history_with_payments(client, payment_setup):
    setup = payment_setup
    # Create a payment first
    await client.post(
        "/api/v1/payments/manual",
        json={
            "booking_id": str(setup["booking"].id),
            "payment_method": "sbp",
        },
        headers=setup["headers"],
    )

    resp = await client.get(
        "/api/v1/payments/history",
        headers=setup["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_payment_history_status_filter(client, payment_setup):
    setup = payment_setup
    # Create a paid payment
    await client.post(
        "/api/v1/payments/manual",
        json={
            "booking_id": str(setup["booking"].id),
            "payment_method": "card_to_card",
        },
        headers=setup["headers"],
    )

    # Filter by status=paid
    resp = await client.get(
        "/api/v1/payments/history",
        params={"status": "paid"},
        headers=setup["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["status"] == "paid"

    # Filter by status=pending (should return empty or fewer)
    resp2 = await client.get(
        "/api/v1/payments/history",
        params={"status": "pending"},
        headers=setup["headers"],
    )
    assert resp2.status_code == 200


# --- Robokassa payment ---


@pytest.mark.asyncio
async def test_create_robokassa_payment_no_credentials(client, payment_setup):
    """Robokassa payment without credentials configured should return 400."""
    setup = payment_setup
    resp = await client.post(
        "/api/v1/payments/robokassa",
        json={"booking_id": str(setup["booking"].id)},
        headers=setup["headers"],
    )
    assert resp.status_code == 400
    assert "robokassa" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_robokassa_payment(client, payment_setup, db_session):
    """Robokassa payment with credentials configured should return 200 with payment_url."""
    setup = payment_setup
    master = setup["master"]

    # Set up Robokassa credentials on the master
    from app.services.encryption_service import encrypt_value

    master.robokassa_merchant_login = "test_merchant"
    master.robokassa_password1_encrypted = encrypt_value("pass1")
    master.robokassa_password2_encrypted = encrypt_value("pass2")
    master.robokassa_is_test = True
    await db_session.flush()

    resp = await client.post(
        "/api/v1/payments/robokassa",
        json={"booking_id": str(setup["booking"].id)},
        headers=setup["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pending"
    assert data["payment_url"] is not None
    assert "robokassa" in data["payment_url"].lower()


# --- Robokassa callback ---


@pytest.mark.asyncio
async def test_robokassa_callback_valid(client, payment_setup, db_session):
    """Robokassa callback with correct signature should return OK{InvId}."""
    import hashlib

    setup = payment_setup
    master = setup["master"]

    from app.services.encryption_service import encrypt_value

    master.robokassa_merchant_login = "test_merchant"
    master.robokassa_password1_encrypted = encrypt_value("pass1")
    master.robokassa_password2_encrypted = encrypt_value("pass2")
    master.robokassa_is_test = True
    master.robokassa_hash_algorithm = "sha256"
    await db_session.flush()

    # Create a robokassa payment
    create_resp = await client.post(
        "/api/v1/payments/robokassa",
        json={"booking_id": str(setup["booking"].id)},
        headers=setup["headers"],
    )
    assert create_resp.status_code == 200
    payment_data = create_resp.json()
    # Extract InvId from payment URL
    import urllib.parse

    parsed = urllib.parse.urlparse(payment_data["payment_url"])
    params = urllib.parse.parse_qs(parsed.query)
    inv_id = params["InvId"][0]
    out_sum = params["OutSum"][0]

    # Compute valid signature: OutSum:InvId:Password#2:Shp_booking_id=X:Shp_master_id=Y
    shp_sorted = sorted([
        f"Shp_booking_id={setup['booking'].id}",
        f"Shp_master_id={master.id}",
    ])
    sig_data = f"{out_sum}:{inv_id}:pass2:{':'.join(shp_sorted)}"
    valid_sig = hashlib.sha256(sig_data.encode("utf-8")).hexdigest()

    resp = await client.post(
        "/webhook/robokassa/result",
        data={
            "OutSum": out_sum,
            "InvId": inv_id,
            "SignatureValue": valid_sig,
            "Shp_master_id": str(master.id),
            "Shp_booking_id": str(setup["booking"].id),
        },
    )
    assert resp.status_code == 200
    assert resp.text == f"OK{inv_id}"


@pytest.mark.asyncio
async def test_robokassa_callback_idempotent(client, payment_setup, db_session):
    """Duplicate callback for same InvId should return OK{InvId} without errors."""
    import hashlib

    setup = payment_setup
    master = setup["master"]

    from app.services.encryption_service import encrypt_value

    master.robokassa_merchant_login = "test_merchant"
    master.robokassa_password1_encrypted = encrypt_value("pass1")
    master.robokassa_password2_encrypted = encrypt_value("pass2")
    master.robokassa_is_test = True
    master.robokassa_hash_algorithm = "sha256"
    await db_session.flush()

    # Create a robokassa payment
    create_resp = await client.post(
        "/api/v1/payments/robokassa",
        json={"booking_id": str(setup["booking"].id)},
        headers=setup["headers"],
    )
    assert create_resp.status_code == 200
    payment_data = create_resp.json()
    import urllib.parse

    parsed = urllib.parse.urlparse(payment_data["payment_url"])
    params = urllib.parse.parse_qs(parsed.query)
    inv_id = params["InvId"][0]
    out_sum = params["OutSum"][0]

    shp_sorted = sorted([
        f"Shp_booking_id={setup['booking'].id}",
        f"Shp_master_id={master.id}",
    ])
    sig_data = f"{out_sum}:{inv_id}:pass2:{':'.join(shp_sorted)}"
    valid_sig = hashlib.sha256(sig_data.encode("utf-8")).hexdigest()

    form_data = {
        "OutSum": out_sum,
        "InvId": inv_id,
        "SignatureValue": valid_sig,
        "Shp_master_id": str(master.id),
        "Shp_booking_id": str(setup["booking"].id),
    }

    # First callback
    resp1 = await client.post("/webhook/robokassa/result", data=form_data)
    assert resp1.status_code == 200
    assert resp1.text == f"OK{inv_id}"

    # Second (duplicate) callback -- should also succeed
    resp2 = await client.post("/webhook/robokassa/result", data=form_data)
    assert resp2.status_code == 200
    assert resp2.text == f"OK{inv_id}"


@pytest.mark.asyncio
async def test_robokassa_callback_invalid_signature(client, payment_setup, db_session):
    """Robokassa callback with wrong signature should return 403."""
    setup = payment_setup
    master = setup["master"]

    from app.services.encryption_service import encrypt_value

    master.robokassa_merchant_login = "test_merchant"
    master.robokassa_password1_encrypted = encrypt_value("pass1")
    master.robokassa_password2_encrypted = encrypt_value("pass2")
    master.robokassa_is_test = True
    await db_session.flush()

    # Create a robokassa payment first
    create_resp = await client.post(
        "/api/v1/payments/robokassa",
        json={"booking_id": str(setup["booking"].id)},
        headers=setup["headers"],
    )
    assert create_resp.status_code == 200

    # Send callback with wrong signature
    resp = await client.post(
        "/webhook/robokassa/result",
        data={
            "OutSum": "1500.00",
            "InvId": "1",
            "SignatureValue": "wrong_signature",
            "Shp_master_id": str(master.id),
            "Shp_booking_id": str(setup["booking"].id),
        },
    )
    assert resp.status_code == 403


# --- Cancel payment ---


@pytest.mark.asyncio
async def test_cancel_payment(client, payment_setup):
    setup = payment_setup
    # Create a payment first
    create_resp = await client.post(
        "/api/v1/payments/manual",
        json={
            "booking_id": str(setup["booking"].id),
            "payment_method": "sbp",
        },
        headers=setup["headers"],
    )
    assert create_resp.status_code == 200
    payment_id = create_resp.json()["id"]

    # Cancel it
    cancel_resp = await client.post(
        f"/api/v1/payments/{payment_id}/cancel",
        headers=setup["headers"],
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"
