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
