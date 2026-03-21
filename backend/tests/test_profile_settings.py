"""Tests for profile settings GET/PUT endpoints + username validation."""

import pytest

from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_get_profile_settings(client, auth_headers):
    headers, master = auth_headers
    resp = await client.get("/api/v1/settings/profile", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == master.name
    assert data["username"] is None
    assert data["specialization"] is None
    assert data["city"] is None


@pytest.mark.asyncio
async def test_update_profile_settings(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.put(
        "/api/v1/settings/profile",
        json={
            "username": "newname",
            "specialization": "Nail Master",
            "city": "Moscow",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "newname"
    assert data["specialization"] == "Nail Master"
    assert data["city"] == "Moscow"


@pytest.mark.asyncio
async def test_username_validation_format(client, auth_headers):
    headers, _ = auth_headers
    # Too short (2 chars)
    resp = await client.put(
        "/api/v1/settings/profile",
        json={"username": "ab"},
        headers=headers,
    )
    assert resp.status_code == 422

    # Contains space
    resp = await client.put(
        "/api/v1/settings/profile",
        json={"username": "has space"},
        headers=headers,
    )
    assert resp.status_code == 422

    # Uppercase
    resp = await client.put(
        "/api/v1/settings/profile",
        json={"username": "UPPER"},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_username_reserved_word(client, auth_headers):
    headers, _ = auth_headers
    for word in ("admin", "api", "m"):
        resp = await client.put(
            "/api/v1/settings/profile",
            json={"username": word},
            headers=headers,
        )
        assert resp.status_code == 422, f"Reserved word '{word}' should be rejected"


@pytest.mark.asyncio
async def test_username_duplicate(client, master_factory, db_session):
    # First master takes "taken"
    master1 = await master_factory(username="taken")
    # Second master tries same username
    master2 = await master_factory()
    token2 = create_access_token(data={"sub": str(master2.id)})
    headers2 = {"Authorization": f"Bearer {token2}"}

    resp = await client.put(
        "/api/v1/settings/profile",
        json={"username": "taken"},
        headers=headers2,
    )
    assert resp.status_code == 409
    assert "already taken" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_username_valid_formats(client, auth_headers):
    headers, _ = auth_headers
    # Simple valid username
    resp = await client.put(
        "/api/v1/settings/profile",
        json={"username": "master_123"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "master_123"

    # Minimum length (3 chars)
    resp = await client.put(
        "/api/v1/settings/profile",
        json={"username": "abc"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "abc"

    # Maximum length (30 chars)
    long_name = "test_user_name_30chars_ok1234"  # 28 chars, within limit
    resp = await client.put(
        "/api/v1/settings/profile",
        json={"username": long_name},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == long_name
