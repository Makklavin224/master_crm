"""Tests for public master page API endpoints."""

import uuid

import pytest

from app.models.client import Client
from app.models.review import Review


@pytest.mark.asyncio
async def test_get_profile_by_username(client, master_factory):
    master = await master_factory(
        name="Anna Stylist",
        username="anna_stylist",
    )
    resp = await client.get(f"/api/v1/masters/{master.username}/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Anna Stylist"
    assert data["username"] == "anna_stylist"
    assert data["avg_rating"] is None
    assert data["review_count"] == 0


@pytest.mark.asyncio
async def test_get_profile_by_uuid(client, master_factory):
    master = await master_factory(name="UUID Master")
    resp = await client.get(f"/api/v1/masters/{master.id}/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "UUID Master"
    assert data["id"] == str(master.id)


@pytest.mark.asyncio
async def test_get_profile_not_found(client):
    resp = await client.get("/api/v1/masters/nonexistent_user/profile")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_services_by_username(
    client, master_factory, service_factory, db_session
):
    master = await master_factory(username="svc_master")
    await service_factory(master_id=master.id, name="Haircut")
    await service_factory(master_id=master.id, name="Coloring")
    resp = await client.get(f"/api/v1/masters/{master.username}/services")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_reviews_by_username(client, master_factory, db_session):
    master = await master_factory(username="review_master")
    # Create a client directly
    test_client = Client(
        phone=f"+7916{uuid.uuid4().hex[:7]}", name="Happy Client"
    )
    db_session.add(test_client)
    await db_session.flush()
    # Create a review
    review = Review(
        master_id=master.id,
        client_id=test_client.id,
        rating=5,
        text="Great service!",
        status="published",
    )
    db_session.add(review)
    await db_session.flush()

    resp = await client.get(f"/api/v1/masters/{master.username}/reviews")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["rating"] == 5
    assert data[0]["client_name"] == "Happy Client"
    assert data[0]["text"] == "Great service!"
