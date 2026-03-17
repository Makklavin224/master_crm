from datetime import timedelta

import pytest

from app.core.security import create_access_token


class TestRegister:
    async def test_register_success(self, client):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "password": "password123",
                "name": "New Master",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(self, client, master_factory):
        await master_factory(email="dup@example.com")
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "dup@example.com",
                "password": "password123",
                "name": "Dup",
            },
        )
        assert resp.status_code == 409

    async def test_register_short_password(self, client):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "short@example.com",
                "password": "short",
                "name": "Short",
            },
        )
        assert resp.status_code == 400

    async def test_register_invalid_email(self, client):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
                "name": "Bad Email",
            },
        )
        assert resp.status_code == 400


class TestLogin:
    async def test_login_success(self, client, master_factory):
        await master_factory(email="login@example.com", password="mypassword1")
        resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "mypassword1",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client, master_factory):
        await master_factory(email="wrong@example.com", password="rightpass1")
        resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrong@example.com",
                "password": "wrongpass1",
            },
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_email(self, client):
        resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nobody@example.com",
                "password": "password123",
            },
        )
        assert resp.status_code == 401


class TestMe:
    async def test_me_authenticated(self, client, auth_headers):
        headers, master = auth_headers
        resp = await client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == master.email
        assert data["name"] == master.name
        assert "hashed_password" not in data

    async def test_me_no_token(self, client):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_me_invalid_token(self, client):
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401

    async def test_me_expired_token(self, client, master_factory):
        master = await master_factory()
        token = create_access_token(
            data={"sub": str(master.id)},
            expires_delta=timedelta(seconds=-1),
        )
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401
