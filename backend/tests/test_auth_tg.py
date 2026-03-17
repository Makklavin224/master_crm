"""Tests for Telegram initData auth endpoint."""

import hashlib
import hmac
import json
import urllib.parse
from datetime import datetime, timezone

import pytest

from app.core.config import settings


def _make_init_data(
    user_id: int = 123456789,
    first_name: str = "Test",
    bot_token: str | None = None,
    tamper: bool = False,
) -> str:
    """
    Create a valid (or tampered) Telegram initData string for testing.
    Follows the Telegram WebApp initData signing protocol.
    """
    if bot_token is None:
        bot_token = settings.tg_bot_token or "test_bot_token:ABC123"

    auth_date = str(int(datetime.now(timezone.utc).timestamp()))
    user_data = json.dumps(
        {
            "id": user_id,
            "first_name": first_name,
            "last_name": "User",
            "language_code": "ru",
        },
        separators=(",", ":"),
    )

    # Build params
    params = {
        "auth_date": auth_date,
        "user": user_data,
        "query_id": "AAGHdF4AAAAAB3ReWN6Grg",
    }

    # Sort alphabetically, join as "key=value\n"
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )

    # Compute HMAC
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256
    ).digest()
    hash_value = hmac.new(
        secret_key, data_check_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    if tamper:
        hash_value = "a" * 64  # Invalid hash

    # Build URL-encoded init_data string
    params["hash"] = hash_value
    return urllib.parse.urlencode(params)


@pytest.mark.asyncio
async def test_tg_auth_valid_initdata(
    client, master_factory, db_session, app_with_db
):
    """POST /auth/tg with valid HMAC-signed initData for a linked master returns JWT."""
    # Override tg_bot_token for test
    original_token = settings.tg_bot_token
    settings.tg_bot_token = "test_bot_token:ABC123"

    try:
        tg_user_id = "123456789"
        master = await master_factory(name="TG Master")
        master.tg_user_id = tg_user_id
        await db_session.flush()

        init_data = _make_init_data(user_id=123456789)

        resp = await client.post(
            "/api/v1/auth/tg",
            json={"init_data": init_data},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    finally:
        settings.tg_bot_token = original_token


@pytest.mark.asyncio
async def test_tg_auth_invalid_hmac(client, app_with_db):
    """POST /auth/tg with tampered initData returns 401."""
    original_token = settings.tg_bot_token
    settings.tg_bot_token = "test_bot_token:ABC123"

    try:
        init_data = _make_init_data(tamper=True)
        resp = await client.post(
            "/api/v1/auth/tg",
            json={"init_data": init_data},
        )
        assert resp.status_code == 401
    finally:
        settings.tg_bot_token = original_token


@pytest.mark.asyncio
async def test_tg_auth_no_linked_master(client, app_with_db):
    """POST /auth/tg with valid initData but no linked master returns 404."""
    original_token = settings.tg_bot_token
    settings.tg_bot_token = "test_bot_token:ABC123"

    try:
        # Use a tg user_id that doesn't match any master
        init_data = _make_init_data(user_id=999999999)
        resp = await client.post(
            "/api/v1/auth/tg",
            json={"init_data": init_data},
        )
        assert resp.status_code == 404
        assert "not linked" in resp.json()["detail"].lower()
    finally:
        settings.tg_bot_token = original_token


@pytest.mark.asyncio
async def test_tg_auth_jwt_works(
    client, master_factory, service_factory, db_session, app_with_db
):
    """Use returned JWT from /auth/tg to call GET /services, verify 200."""
    original_token = settings.tg_bot_token
    settings.tg_bot_token = "test_bot_token:ABC123"

    try:
        tg_user_id = "111222333"
        master = await master_factory(name="JWT TG Master")
        master.tg_user_id = tg_user_id
        await db_session.flush()

        # Create a service for this master
        await service_factory(master.id, name="TG Service")

        init_data = _make_init_data(user_id=111222333)
        auth_resp = await client.post(
            "/api/v1/auth/tg",
            json={"init_data": init_data},
        )
        assert auth_resp.status_code == 200
        token = auth_resp.json()["access_token"]

        # Use the JWT to access services
        svc_resp = await client.get(
            "/api/v1/services",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert svc_resp.status_code == 200
    finally:
        settings.tg_bot_token = original_token
