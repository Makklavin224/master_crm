"""Tests for Service CRUD endpoints."""

import pytest


@pytest.mark.asyncio
async def test_create_service(client, auth_headers):
    headers, master = auth_headers
    resp = await client.post(
        "/api/v1/services",
        json={
            "name": "Haircut",
            "duration_minutes": 60,
            "price": 250000,
            "category": "Hair",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Haircut"
    assert data["duration_minutes"] == 60
    assert data["price"] == 250000
    assert data["category"] == "Hair"
    assert data["is_active"] is True
    assert data["master_id"] == str(master.id)


@pytest.mark.asyncio
async def test_list_services(client, auth_headers, service_factory):
    headers, master = auth_headers
    # Set RLS context so service_factory inserts are visible
    await service_factory(master.id, name="Service A")
    await service_factory(master.id, name="Service B")

    resp = await client.get("/api/v1/services", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    names = [s["name"] for s in data]
    assert "Service A" in names
    assert "Service B" in names


@pytest.mark.asyncio
async def test_update_service(client, auth_headers, service_factory):
    headers, master = auth_headers
    svc = await service_factory(master.id, name="Old Name")

    resp = await client.put(
        f"/api/v1/services/{svc.id}",
        json={"name": "New Name", "price": 300000},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "New Name"
    assert data["price"] == 300000


@pytest.mark.asyncio
async def test_delete_service(client, auth_headers, service_factory):
    headers, master = auth_headers
    svc = await service_factory(master.id, name="To Delete")

    resp = await client.delete(f"/api/v1/services/{svc.id}", headers=headers)
    assert resp.status_code == 204

    # Verify service no longer appears in active list
    resp = await client.get("/api/v1/services", headers=headers)
    names = [s["name"] for s in resp.json()]
    assert "To Delete" not in names


@pytest.mark.asyncio
async def test_create_service_without_name(client, auth_headers):
    headers, _ = auth_headers
    resp = await client.post(
        "/api/v1/services",
        json={"duration_minutes": 60, "price": 100000},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_public_service_list(client, auth_headers, service_factory):
    _, master = auth_headers
    await service_factory(master.id, name="Public Service")

    # Public endpoint -- no auth headers
    resp = await client.get(f"/api/v1/masters/{master.id}/services")
    assert resp.status_code == 200
    data = resp.json()
    names = [s["name"] for s in data]
    assert "Public Service" in names


@pytest.mark.asyncio
async def test_create_service_requires_auth(client):
    resp = await client.post(
        "/api/v1/services",
        json={"name": "Haircut", "duration_minutes": 60, "price": 250000},
    )
    assert resp.status_code == 401
