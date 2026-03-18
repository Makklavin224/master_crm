"""Tests for Master settings GET/PUT endpoints."""

import pytest


@pytest.mark.asyncio
async def test_get_settings_defaults(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.get("/api/v1/settings", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["buffer_minutes"] == 0
    assert data["cancellation_deadline_hours"] == 24
    assert data["slot_interval_minutes"] == 30


@pytest.mark.asyncio
async def test_update_settings(client, auth_headers):
    headers, _ = auth_headers

    # Update buffer_minutes
    resp = await client.put(
        "/api/v1/settings",
        json={"buffer_minutes": 15},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["buffer_minutes"] == 15

    # GET confirms persistence
    get_resp = await client.get("/api/v1/settings", headers=headers)
    assert get_resp.json()["buffer_minutes"] == 15


@pytest.mark.asyncio
async def test_update_settings_partial(client, auth_headers):
    headers, _ = auth_headers

    # Only update cancellation_deadline_hours
    resp = await client.put(
        "/api/v1/settings",
        json={"cancellation_deadline_hours": 12},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["cancellation_deadline_hours"] == 12
    # Other fields unchanged
    assert data["buffer_minutes"] == 0
    assert data["slot_interval_minutes"] == 30


@pytest.mark.asyncio
async def test_settings_requires_auth(client):
    resp = await client.get("/api/v1/settings")
    assert resp.status_code == 401


# --- Payment settings ---


@pytest.mark.asyncio
async def test_get_payment_settings(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.get("/api/v1/settings/payment", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_robokassa"] is False
    assert data["fiscalization_level"] == "none"
    assert data["has_seen_grey_warning"] is False
    assert data["receipt_sno"] == "patent"


@pytest.mark.asyncio
async def test_update_payment_settings(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.put(
        "/api/v1/settings/payment",
        json={
            "card_number": "2200123456789012",
            "sbp_phone": "+79161234567",
            "bank_name": "Tinkoff",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["card_number"] == "2200123456789012"
    assert data["sbp_phone"] == "+79161234567"
    assert data["bank_name"] == "Tinkoff"


@pytest.mark.asyncio
async def test_setup_robokassa(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.post(
        "/api/v1/settings/payment/robokassa",
        json={
            "merchant_login": "my_shop",
            "password1": "secret1",
            "password2": "secret2",
            "is_test": True,
            "hash_algorithm": "sha256",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_robokassa"] is True
    assert data["robokassa_is_test"] is True


@pytest.mark.asyncio
async def test_disconnect_robokassa(client, auth_headers):
    headers, _ = auth_headers
    # First connect
    await client.post(
        "/api/v1/settings/payment/robokassa",
        json={
            "merchant_login": "my_shop",
            "password1": "secret1",
            "password2": "secret2",
        },
        headers=headers,
    )
    # Then disconnect
    resp = await client.delete(
        "/api/v1/settings/payment/robokassa",
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["has_robokassa"] is False


@pytest.mark.asyncio
async def test_grey_warning_flag(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.post(
        "/api/v1/settings/payment/grey-warning-seen",
        headers=headers,
    )
    assert resp.status_code == 204

    # Verify flag persisted
    get_resp = await client.get("/api/v1/settings/payment", headers=headers)
    assert get_resp.json()["has_seen_grey_warning"] is True


@pytest.mark.asyncio
async def test_fiscalization_levels(client, auth_headers):
    headers, _ = auth_headers
    for level in ("none", "manual", "auto"):
        resp = await client.put(
            "/api/v1/settings/payment",
            json={"fiscalization_level": level},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["fiscalization_level"] == level
